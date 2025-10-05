"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import Logo from "@/components/Logo";
import {
  IconArrowRight,
  IconBrain,
  IconBoltFilled,
  IconFlameFilled,
} from "@tabler/icons-react";

export default function IntroPage() {
  const router = useRouter();
  const [isVisible, setIsVisible] = useState(false);
  const [showElements, setShowElements] = useState(false);

  useEffect(() => {
    // Trigger animations on mount
    const timer1 = setTimeout(() => setIsVisible(true), 100);
    const timer2 = setTimeout(() => setShowElements(true), 800);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
    };
  }, []);

  const handleGetStarted = () => {
    localStorage.setItem("hasSeenIntro", "true");
    router.push("/");
  };

  return (
    <div className="min-h-screen bg-grid-pattern flex flex-col items-center justify-center relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Floating brain icons */}
        <div
          className={`absolute top-20 left-10 text-cyan-400/20 transition-all duration-2000 ${
            showElements ? "animate-pulse" : "opacity-0"
          }`}
          style={{ animationDelay: "0s" }}
        >
          <IconBrain className="h-16 w-16" />
        </div>
        <div
          className={`absolute top-40 right-20 text-cyan-400/15 transition-all duration-2000 ${
            showElements ? "animate-pulse" : "opacity-0"
          }`}
          style={{ animationDelay: "1s" }}
        >
          <IconBoltFilled className="h-12 w-12" />
        </div>
        <div
          className={`absolute bottom-32 left-20 text-cyan-400/10 transition-all duration-2000 ${
            showElements ? "animate-pulse" : "opacity-0"
          }`}
          style={{ animationDelay: "2s" }}
        >
          <IconFlameFilled className="h-20 w-20" />
        </div>
        <div
          className={`absolute bottom-20 right-32 text-cyan-400/20 transition-all duration-2000 ${
            showElements ? "animate-pulse" : "opacity-0"
          }`}
          style={{ animationDelay: "1.5s" }}
        >
          <IconBrain className="h-14 w-14" />
        </div>
      </div>

      {/* Main content */}
      <div className="text-center z-10 max-w-4xl mx-auto px-6">
        {/* Logo with animation */}
        <div
          className={`mb-8 transition-all duration-1000 ${
            isVisible ? "opacity-100 scale-100" : "opacity-0 scale-95"
          }`}
        >
          <Logo size="lg" showText={false} className="justify-center" />
        </div>

        {/* Title with stagger animation */}
        <h1
          className={`text-7xl md:text-8xl font-bold text-foreground mb-6 transition-all duration-1000 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
          style={{
            transitionDelay: "200ms",
            fontFamily: "var(--font-space-grotesk)",
            letterSpacing: "-0.02em",
          }}
        >
          BRAINLATTICE
        </h1>

        {/* Punchline with animation */}
        <div
          className={`mb-12 transition-all duration-1000 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
          style={{ transitionDelay: "400ms" }}
        >
          <p className="text-2xl md:text-3xl font-light mb-4 font-mono">
            Your hell textbook just became ✨
            <span className="italic font-serif text-cyan-400">
              comeback mode
            </span>
            ✨
          </p>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto font-light">
            Drop that <span>200-page nightmare</span> → Get an{" "}
            <span className="italic font-serif text-cyan-400">
              actual brain map
            </span>{" "}
            that makes sense
            <br />
            <span className="text-cyan-400 font-mono text-sm mt-2 block">
              No cap, this is straight fire 🔥
            </span>
          </p>
        </div>

        {/* CTA Button with animation */}
        <div
          className={`transition-all duration-1000 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
          style={{ transitionDelay: "600ms" }}
        >
          <Button
            onClick={handleGetStarted}
            size="lg"
            className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold px-12 py-6 text-xl rounded-sm border-glow-cyan transition-all duration-300 hover:scale-105 font-mono tracking-wide"
          >
            LET'S GET <span className="italic font-serif">COOKING</span>
            <IconArrowRight className="ml-2 h-6 w-6" />
          </Button>
        </div>

        {/* Subtitle */}
        <div
          className={`mt-8 transition-all duration-1000 ${
            isVisible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
          style={{ transitionDelay: "800ms" }}
        >
          <p className="text-sm text-muted-foreground/70 font-mono">
            Stop suffering through{" "}
            <span className="text-cyan-400">unreadable walls of text</span> •
            Start actually{" "}
            <span className="font-bold">understanding stuff</span>
          </p>
        </div>
      </div>
    </div>
  );
}
