"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  className?: string;
}

export default function Logo({
  size = "md",
  showText = true,
  className = "",
}: LogoProps) {
  const [isHovered, setIsHovered] = useState(false);

  const sizeClasses = {
    sm: "h-6 w-6",
    md: "h-9 w-9",
    lg: "h-12 w-12",
  };

  const textSizes = {
    sm: "text-lg",
    md: "text-2xl",
    lg: "text-3xl",
  };

  return (
    <Link
      href="/"
      className={`flex items-center space-x-3 cursor-pointer ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="relative">
        <Image
          src="/favicon.svg"
          alt="BrainLattice Logo"
          width={size === "sm" ? 24 : size === "md" ? 36 : 48}
          height={size === "sm" ? 24 : size === "md" ? 36 : 48}
          className={`${sizeClasses[size]} transition-transform duration-300 ${
            isHovered ? "scale-110" : "scale-100"
          }`}
          priority
        />
        {/* Glow effect overlay */}
        <div
          className={`absolute inset-0 ${
            sizeClasses[size]
          } transition-opacity duration-300 ${
            isHovered ? "opacity-50" : "opacity-0"
          }`}
          style={{
            filter: "drop-shadow(0 0 10px oklch(0.7 0.2 195 / 0.5))",
          }}
        >
          <Image
            src="/favicon.svg"
            alt=""
            width={size === "sm" ? 24 : size === "md" ? 36 : 48}
            height={size === "sm" ? 24 : size === "md" ? 36 : 48}
            className={sizeClasses[size]}
          />
        </div>
      </div>

      {showText && (
        <h1
          className={`font-bold tracking-tight text-cyan-400 text-glow-cyan font-mono ${textSizes[size]}`}
        >
          BrainLattice
        </h1>
      )}
    </Link>
  );
}
