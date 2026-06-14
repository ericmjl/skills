import React from "react";
import { Composition } from "remotion";
import { Typewriter } from "./Typewriter";
import { ChineseDemo } from "./ChineseDemo";
import { ThemeShowcase } from "./ThemeShowcase";
import { ExcalidrawDemo } from "./ExcalidrawDemo";
import {
    ivoryTheme,
    darkEditorTheme,
    chalkBlackboardTheme,
    paperNotebookTheme,
    retroTerminalTheme,
    spotlightTheme,
    lcdTerminalTheme,
    pixelArtTheme,
} from "./themes";
import { PORTRAIT } from "./layout";
import "./index.css";

const FPS = 30000 / 1001; // NTSC 29.97fps — matches camera footage for A-roll sync
const DURATION_SECONDS = 70;
const frames = (s: number) => Math.ceil(FPS * s); // seconds → integer frame count

export const RemotionRoot: React.FC = () => {
    return (
        <>
            {/* Default demo (ivory theme) */}
            <Composition
                id="Typewriter"
                component={Typewriter}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1920}
                height={1080}
            />
            <Composition
                id="ChineseDemo"
                component={ChineseDemo}
                durationInFrames={frames(75)}
                fps={FPS}
                width={1920}
                height={1080}
            />

            {/* Theme showcase: cycles through all 6 themes */}
            <Composition
                id="ThemeShowcase"
                component={ThemeShowcase}
                durationInFrames={frames(30)}
                fps={FPS}
                width={1920}
                height={1080}
            />

            {/* Excalidraw drawing layer demo */}
            <Composition
                id="ExcalidrawDemo"
                component={ExcalidrawDemo}
                durationInFrames={frames(20)}
                fps={FPS}
                width={1920}
                height={1080}
            />

            {/* Individual theme previews */}
            <Composition
                id="Theme-DarkEditor"
                component={() => <Typewriter theme={darkEditorTheme} />}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1920}
                height={1080}
            />
            <Composition
                id="Theme-ChalkBlackboard"
                component={() => <Typewriter theme={chalkBlackboardTheme} />}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1920}
                height={1080}
            />
            <Composition
                id="Theme-PaperNotebook"
                component={() => <Typewriter theme={paperNotebookTheme} />}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1920}
                height={1080}
            />
            <Composition
                id="Theme-RetroTerminal"
                component={() => <Typewriter theme={retroTerminalTheme} />}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1920}
                height={1080}
            />
            <Composition
                id="Theme-Spotlight"
                component={() => <Typewriter theme={spotlightTheme} />}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1920}
                height={1080}
            />
            <Composition
                id="Theme-LCDTerminal"
                component={() => <Typewriter theme={lcdTerminalTheme} />}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1920}
                height={1080}
            />
            <Composition
                id="Theme-PixelArt"
                component={() => <Typewriter theme={pixelArtTheme} />}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1920}
                height={1080}
            />

            {/* ── Portrait (9:16) compositions ── */}
            <Composition
                id="Typewriter-Portrait"
                component={() => <Typewriter layout={PORTRAIT} />}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1080}
                height={1920}
            />
            <Composition
                id="Theme-DarkEditor-Portrait"
                component={() => <Typewriter theme={darkEditorTheme} layout={PORTRAIT} />}
                durationInFrames={frames(DURATION_SECONDS)}
                fps={FPS}
                width={1080}
                height={1920}
            />
        </>
    );
};
