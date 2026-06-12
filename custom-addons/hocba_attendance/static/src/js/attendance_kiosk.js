/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";

const MODELS_URL = "/hocba_employees/static/lib/face-api/models";

export class AttendanceKiosk extends Component {
    static template = "hocba_attendance.AttendanceKiosk";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.videoRef = useRef("video");
        this.canvasRef = useRef("canvas");
        this.state = useState({
            ready: false,
            busy: false,
            enrolled: false,
            applicable: false,
            employeeName: "",
            message: "Đang khởi tạo...",
        });
        this._stream = null;

        onWillStart(async () => {
            try {
                await this._loadFaceApi();
                await this._loadEmployee();
            } catch (e) {
                this.state.message =
                    "Không tải được nhận diện khuôn mặt. Tải lại trang hoặc kiểm tra kết nối.";
            }
        });
        onMounted(() => this._startCamera());
        onWillUnmount(() => this._stopCamera());
    }

    async _loadFaceApi() {
        if (!window.faceapi) {
            await new Promise((resolve, reject) => {
                const s = document.createElement("script");
                s.src = "/hocba_employees/static/lib/face-api/face-api.min.js";
                s.onload = resolve;
                s.onerror = reject;
                document.head.appendChild(s);
            });
        }
        const faceapi = window.faceapi;
        await faceapi.nets.tinyFaceDetector.loadFromUri(MODELS_URL);
        await faceapi.nets.faceLandmark68Net.loadFromUri(MODELS_URL);
        await faceapi.nets.faceRecognitionNet.loadFromUri(MODELS_URL);
    }

    async _loadEmployee() {
        const emp = await this.orm.call("hr.employee", "get_self_attendance_info", []);
        this.state.employeeName = emp.name || "";
        this.state.enrolled = !!emp.enrolled;
        this.state.applicable = !!emp.is_official;
        this.state.ready = true;
        if (!this.state.applicable) {
            this.state.message =
                "Chức năng điểm danh chỉ áp dụng cho nhân viên chính thức.";
        } else {
            this.state.message = this.state.enrolled
                ? "Sẵn sàng điểm danh"
                : "Bạn chưa đăng ký khuôn mặt — bấm Đăng ký để chụp ảnh mẫu.";
        }
    }

    async _startCamera() {
        try {
            this._stream = await navigator.mediaDevices.getUserMedia({ video: true });
            this.videoRef.el.srcObject = this._stream;
        } catch (e) {
            this.state.message = "Không truy cập được camera. Cần HTTPS/localhost và cấp quyền.";
        }
    }

    _stopCamera() {
        if (this._stream) {
            this._stream.getTracks().forEach((t) => t.stop());
            this._stream = null;
        }
    }

    _capturePhotoDataUrl() {
        const video = this.videoRef.el;
        const canvas = this.canvasRef.el;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext("2d").drawImage(video, 0, 0);
        return canvas.toDataURL("image/jpeg", 0.85);
    }

    async _computeDescriptor() {
        const faceapi = window.faceapi;
        const det = await faceapi
            .detectSingleFace(this.videoRef.el, new faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptor();
        return det ? Array.from(det.descriptor) : null;
    }

    _getLocation() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve({ latitude: 0, longitude: 0 });
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (pos) => resolve({
                    latitude: pos.coords.latitude,
                    longitude: pos.coords.longitude,
                }),
                () => resolve({ latitude: 0, longitude: 0 }),
                { enableHighAccuracy: true, timeout: 8000 }
            );
        });
    }

    async _captureCommon() {
        if (!this._stream) {
            this.notification.add(
                "Camera chưa sẵn sàng. Hãy cấp quyền camera và thử lại.",
                { type: "warning" });
            return null;
        }
        const descriptor = await this._computeDescriptor();
        if (!descriptor) {
            this.notification.add("Không phát hiện khuôn mặt. Thử lại.", { type: "warning" });
            return null;
        }
        const dataUrl = this._capturePhotoDataUrl();
        const photo = dataUrl.split(",")[1]; // strip data: prefix -> base64
        const loc = await this._getLocation();
        return { descriptor, photo, latitude: loc.latitude, longitude: loc.longitude };
    }

    async onEnroll() {
        this.state.busy = true;
        try {
            const cap = await this._captureCommon();
            if (!cap) return;
            await this.orm.call("hr.employee", "enroll_self_face", [
                { photo: cap.photo, descriptor: cap.descriptor },
            ]);
            this.state.enrolled = true;
            this.state.message = "Đăng ký khuôn mặt thành công.";
            this.notification.add("Đã lưu khuôn mặt mẫu.", { type: "success" });
        } catch (e) {
            this.notification.add("Đăng ký thất bại. Vui lòng thử lại.", { type: "danger" });
        } finally {
            this.state.busy = false;
        }
    }

    async _check(kind) {
        if (!this.state.enrolled) {
            this.notification.add("Hãy đăng ký khuôn mặt trước.", { type: "warning" });
            return;
        }
        this.state.busy = true;
        try {
            const cap = await this._captureCommon();
            if (!cap) return;
            const method = kind === "in" ? "action_check_in" : "action_check_out";
            const res = await this.orm.call("hocba.attendance", method, [cap]);
            const flags = [];
            if (res.face_suspect) flags.push("khuôn mặt nghi ngờ");
            if (res.out_of_zone) flags.push("ngoài vùng văn phòng");
            if (res.out_of_window) flags.push("ngoài khung giờ");
            const msg = (kind === "in" ? "Đã check-in" : "Đã check-out")
                + (flags.length ? " (⚠ " + flags.join(", ") + ")" : " thành công");
            this.notification.add(msg, { type: flags.length ? "warning" : "success" });
        } catch (e) {
            this.notification.add("Điểm danh thất bại. Vui lòng thử lại.", { type: "danger" });
        } finally {
            this.state.busy = false;
        }
    }

    onCheckIn() { return this._check("in"); }
    onCheckOut() { return this._check("out"); }
}

registry.category("actions").add("hocba_attendance_kiosk", AttendanceKiosk);
