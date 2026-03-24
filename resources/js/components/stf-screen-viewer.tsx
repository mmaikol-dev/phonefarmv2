import { useEffect, useRef, useState } from 'react';

type Props = {
    height: number;
    width: number;
    websocketUrl: string;
};

export default function StfScreenViewer({
    height,
    width,
    websocketUrl,
}: Props) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const imageRef = useRef<HTMLImageElement | null>(null);
    const objectUrlRef = useRef<string | null>(null);
    const websocketRef = useRef<WebSocket | null>(null);
    const [hasFrame, setHasFrame] = useState(false);

    useEffect(() => {
        imageRef.current = new Image();

        return () => {
            if (objectUrlRef.current) {
                URL.revokeObjectURL(objectUrlRef.current);
            }
        };
    }, []);

    useEffect(() => {
        const canvas = canvasRef.current;
        const wrapper = wrapperRef.current;
        const image = imageRef.current;

        if (!canvas || !wrapper || !image) {
            return;
        }

        const context = canvas.getContext('2d');

        if (!context) {
            return;
        }

        const websocket = new WebSocket(websocketUrl);
        websocket.binaryType = 'blob';
        websocketRef.current = websocket;

        const sendCurrentSize = () => {
            if (websocket.readyState !== WebSocket.OPEN || !wrapper) {
                return;
            }

            const wrapperWidth = Math.max(1, Math.floor(wrapper.clientWidth));
            const renderedHeight = Math.max(
                1,
                Math.floor((wrapperWidth * height) / width),
            );

            websocket.send(`size ${wrapperWidth}x${renderedHeight}`);
        };

        const observer = new ResizeObserver(() => {
            sendCurrentSize();
        });

        observer.observe(wrapper);

        image.onload = () => {
            canvas.width = image.width;
            canvas.height = image.height;
            context.drawImage(image, 0, 0);
            setHasFrame(true);

            if (objectUrlRef.current) {
                URL.revokeObjectURL(objectUrlRef.current);
                objectUrlRef.current = null;
            }
        };

        websocket.onopen = () => {
            sendCurrentSize();
            websocket.send('on');
        };

        websocket.onmessage = (event) => {
            if (!(event.data instanceof Blob)) {
                return;
            }

            if (objectUrlRef.current) {
                URL.revokeObjectURL(objectUrlRef.current);
            }

            objectUrlRef.current = URL.createObjectURL(event.data);
            image.src = objectUrlRef.current;
        };

        return () => {
            observer.disconnect();

            if (websocket.readyState === WebSocket.OPEN) {
                websocket.send('off');
            }

            websocket.close();
            websocketRef.current = null;
        };
    }, [height, websocketUrl, width]);

    return (
        <div ref={wrapperRef} className="relative size-full bg-black">
            <canvas
                ref={canvasRef}
                className="size-full object-contain"
                style={{ imageRendering: 'auto' }}
            />

            {!hasFrame ? (
                <div className="absolute inset-0 flex items-center justify-center bg-black/80 text-sm text-slate-300">
                    Connecting to STF screen stream...
                </div>
            ) : null}
        </div>
    );
}
