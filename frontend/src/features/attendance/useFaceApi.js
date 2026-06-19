/* Nạp face-api.js (đã vendor ở hocba_employees) + camera + GPS.
   Tách riêng để CheckInPanel không phải biết chi tiết thư viện. */
import { useEffect, useRef, useState } from 'react';

const LIB = '/hocba_employees/static/lib/face-api/face-api.min.js';
const MODELS = '/hocba_employees/static/lib/face-api/models';

let _libPromise = null;
function loadFaceApi() {
  if (window.faceapi && window.faceapi.nets.faceRecognitionNet.params) {
    return Promise.resolve(window.faceapi);
  }
  if (_libPromise) return _libPromise;
  _libPromise = new Promise((resolve, reject) => {
    if (window.faceapi) return resolve();
    const s = document.createElement('script');
    s.src = LIB; s.onload = resolve; s.onerror = reject;
    document.head.appendChild(s);
  }).then(async () => {
    const f = window.faceapi;
    await f.nets.tinyFaceDetector.loadFromUri(MODELS);
    await f.nets.faceLandmark68Net.loadFromUri(MODELS);
    await f.nets.faceRecognitionNet.loadFromUri(MODELS);
    return f;
  });
  return _libPromise;
}

function getLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve({ lat: 0, lng: 0 });
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lng: p.coords.longitude }),
      () => resolve({ lat: 0, lng: 0 }),
      { enableHighAccuracy: true, timeout: 8000 });
  });
}

export function useFaceApi() {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [camError, setCamError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    loadFaceApi()
      .then(() => navigator.mediaDevices.getUserMedia({ video: true }))
      .then((stream) => {
        if (cancelled) { stream.getTracks().forEach((t) => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setReady(true);
      })
      .catch(() => setCamError(
        'Không mở được camera hoặc thư viện nhận diện. Cần HTTPS/localhost và cấp quyền camera.'));
    return () => {
      cancelled = true;
      if (streamRef.current) streamRef.current.getTracks().forEach((t) => t.stop());
    };
  }, []);

  /* Trả {descriptor, photo, latitude, longitude} hoặc {error:'no_face'} / null. */
  async function capture() {
    const faceapi = window.faceapi;
    const video = videoRef.current;
    if (!faceapi || !video || !streamRef.current) return null;
    const det = await faceapi
      .detectSingleFace(video, new faceapi.TinyFaceDetectorOptions())
      .withFaceLandmarks()
      .withFaceDescriptor();
    if (!det) return { error: 'no_face' };
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const photo = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
    const loc = await getLocation();
    return {
      descriptor: Array.from(det.descriptor), photo,
      latitude: loc.lat, longitude: loc.lng,
    };
  }

  return { videoRef, ready, camError, capture };
}
