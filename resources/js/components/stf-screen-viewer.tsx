import { io, type Socket } from 'socket.io-client';
import { useEffect, useRef, useState } from 'react';

type Props = {
    controlSocketUrl: string;
    deviceChannel: string;
    height: number;
    sessionBootstrapUrl?: string | null;
    width: number;
    websocketUrl: string;
};

export default function StfScreenViewer({
    controlSocketUrl,
    deviceChannel,
    height,
    sessionBootstrapUrl,
    width,
    websocketUrl,
}: Props) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const imageRef = useRef<HTMLImageElement | null>(null);
    const objectUrlRef = useRef<string | null>(null);
    const controlSocketRef = useRef<Socket | null>(null);
    const activeTouchRef = useRef(false);
    const sequenceRef = useRef(0);
    const [hasFrame, setHasFrame] = useState(false);
    const [bootstrapReady, setBootstrapReady] = useState(!sessionBootstrapUrl);
    const [controlReady, setControlReady] = useState(false);

    const nextSequence = () => {
        sequenceRef.current += 1;

        return sequenceRef.current;
    };

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
        };
    }, [height, websocketUrl, width]);

    useEffect(() => {
        if (!controlSocketUrl || !deviceChannel || !bootstrapReady) {
            return;
        }

        const socket = io(controlSocketUrl, {
            reconnection: false,
            transports: ['websocket'],
            withCredentials: true,
        });

        controlSocketRef.current = socket;

        socket.on('connect', () => {
            setControlReady(true);
        });

        socket.on('connect_error', () => {
            setControlReady(false);
        });

        socket.on('disconnect', () => {
            setControlReady(false);
        });

        return () => {
            controlSocketRef.current?.close();
            controlSocketRef.current = null;
            setControlReady(false);
        };
    }, [bootstrapReady, controlSocketUrl, deviceChannel]);

    const getNormalizedPosition = (event: React.PointerEvent<HTMLDivElement>) => {
        const bounds = event.currentTarget.getBoundingClientRect();
        const x = Math.min(Math.max((event.clientX - bounds.left) / bounds.width, 0), 1);
        const y = Math.min(Math.max((event.clientY - bounds.top) / bounds.height, 0), 1);

        return { x, y };
    };

    const emitTouch = (eventName: string, payload: Record<string, unknown>) => {
        const socket = controlSocketRef.current;

        if (!socket?.connected) {
            return;
        }

        socket.emit(eventName, deviceChannel, payload);
    };

    const handlePointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
        const position = getNormalizedPosition(event);

        activeTouchRef.current = true;
        event.currentTarget.setPointerCapture(event.pointerId);

        emitTouch('input.touchDown', {
            contact: 0,
            pressure: 0.5,
            seq: nextSequence(),
            x: position.x,
            y: position.y,
        });
        emitTouch('input.touchCommit', {
            seq: nextSequence(),
        });
    };

    const handlePointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
        if (!activeTouchRef.current) {
            return;
        }

        const position = getNormalizedPosition(event);

        emitTouch('input.touchMove', {
            contact: 0,
            pressure: 0.5,
            seq: nextSequence(),
            x: position.x,
            y: position.y,
        });
        emitTouch('input.touchCommit', {
            seq: nextSequence(),
        });
    };

    const handlePointerUp = (event: React.PointerEvent<HTMLDivElement>) => {
        if (!activeTouchRef.current) {
            return;
        }

        activeTouchRef.current = false;

        if (event.currentTarget.hasPointerCapture(event.pointerId)) {
            event.currentTarget.releasePointerCapture(event.pointerId);
        }

        emitTouch('input.touchUp', {
            contact: 0,
            seq: nextSequence(),
        });
        emitTouch('input.touchCommit', {
            seq: nextSequence(),
        });
    };

    return (
        <div
            ref={wrapperRef}
            className="relative size-full bg-black"
            onPointerDown={handlePointerDown}
            onPointerMove={handlePointerMove}
            onPointerUp={handlePointerUp}
            onPointerCancel={handlePointerUp}
            style={{ touchAction: 'none' }}
        >
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

            {!controlReady && hasFrame ? (
                <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-black/70 px-3 py-2 text-center text-xs text-slate-300">
                    Screen is live. Touch controls are still connecting...
                </div>
            ) : null}

            {sessionBootstrapUrl ? (
                <iframe
                    title="STF session bootstrap"
                    src={sessionBootstrapUrl}
                    className="hidden"
                    onLoad={() => setBootstrapReady(true)}
                />
            ) : null}
        </div>
    );
}
