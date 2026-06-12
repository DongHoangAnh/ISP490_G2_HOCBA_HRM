/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

const MODELS_URL = "/hocba_attendance/static/lib/face-api/models";

export class FaceDescriptorField extends Component {
    static template = "hocba_attendance.FaceDescriptorField";
    static props = { ...standardFieldProps, imageField: { type: String, optional: true } };

    setup() {
        this.notification = useService("notification");
        onWillStart(() => this._loadFaceApi());
    }

    async _loadFaceApi() {
        if (!window.faceapi) {
            await new Promise((resolve, reject) => {
                const s = document.createElement("script");
                s.src = "/hocba_attendance/static/lib/face-api/face-api.min.js";
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

    get hasDescriptor() {
        return !!this.props.record.data[this.props.name];
    }

    async onCompute() {
        const imageField = this.props.imageField || "x_face_image";
        const b64 = this.props.record.data[imageField];
        if (!b64) {
            this.notification.add("Hãy tải ảnh khuôn mặt trước.", { type: "warning" });
            return;
        }
        const img = new Image();
        img.src = "data:image/png;base64," + b64;
        await img.decode();
        const faceapi = window.faceapi;
        const det = await faceapi
            .detectSingleFace(img, new faceapi.TinyFaceDetectorOptions())
            .withFaceLandmarks()
            .withFaceDescriptor();
        if (!det) {
            this.notification.add("Không phát hiện khuôn mặt trong ảnh.", { type: "danger" });
            return;
        }
        await this.props.record.update({
            [this.props.name]: JSON.stringify(Array.from(det.descriptor)),
        });
        this.notification.add("Đã tính vector khuôn mặt. Nhớ Lưu.", { type: "success" });
    }
}

export const faceDescriptorField = {
    component: FaceDescriptorField,
    supportedTypes: ["text"],
    extractProps: ({ options }) => ({ imageField: options.image_field }),
};

registry.category("fields").add("hocba_face_descriptor", faceDescriptorField);
