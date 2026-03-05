"use client";

import { useEffect, useRef, useState } from "react";

interface AnimatedNumberProps {
    value: number;
    duration?: number;
    className?: string;
}

/**
 * Smoothly animates from the previous value to the new value.
 * Uses requestAnimationFrame for buttery-smooth transitions.
 */
export function AnimatedNumber({ value, duration = 600, className }: AnimatedNumberProps) {
    const [displayValue, setDisplayValue] = useState(value);
    const previousValue = useRef(value);
    const animationRef = useRef<number | null>(null);

    useEffect(() => {
        const from = previousValue.current;
        const to = value;
        previousValue.current = value;

        if (from === to) return;

        const startTime = performance.now();

        const animate = (currentTime: number) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease-out cubic for natural deceleration
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(from + (to - from) * eased);

            setDisplayValue(current);

            if (progress < 1) {
                animationRef.current = requestAnimationFrame(animate);
            }
        };

        animationRef.current = requestAnimationFrame(animate);

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [value, duration]);

    return <span className={className}>{displayValue}</span>;
}
