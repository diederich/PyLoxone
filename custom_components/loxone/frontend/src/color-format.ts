import type { HassState } from "./types";

export interface RgbColor {
  r: number;
  g: number;
  b: number;
}

const HSV_PATTERN =
  /^hsv\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)$/i;

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function normalizeByte(value: unknown): number | null {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return null;
  }
  return Math.round(clamp(value, 0, 255));
}

function tupleFromUnknown(value: unknown): [number, number, number] | null {
  if (!Array.isArray(value) || value.length < 3) {
    return null;
  }
  const r = normalizeByte(value[0]);
  const g = normalizeByte(value[1]);
  const b = normalizeByte(value[2]);
  if (r === null || g === null || b === null) {
    return null;
  }
  return [r, g, b];
}

export function hsvToRgb(hue: number, saturation: number, value: number): RgbColor {
  const h = ((hue % 360) + 360) % 360;
  const s = clamp(saturation, 0, 100) / 100;
  const v = clamp(value, 0, 100) / 100;
  const c = v * s;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = v - c;

  let red = 0;
  let green = 0;
  let blue = 0;
  if (h < 60) {
    red = c;
    green = x;
  } else if (h < 120) {
    red = x;
    green = c;
  } else if (h < 180) {
    green = c;
    blue = x;
  } else if (h < 240) {
    green = x;
    blue = c;
  } else if (h < 300) {
    red = x;
    blue = c;
  } else {
    red = c;
    blue = x;
  }

  return {
    r: Math.round((red + m) * 255),
    g: Math.round((green + m) * 255),
    b: Math.round((blue + m) * 255),
  };
}

export function rgbFromHassState(state: HassState | undefined): RgbColor | null {
  if (!state || state.state === "unavailable" || state.state === "unknown") {
    return null;
  }

  const rgb = tupleFromUnknown(state.attributes.rgb_color);
  if (rgb) {
    return { r: rgb[0], g: rgb[1], b: rgb[2] };
  }

  const hs = state.attributes.hs_color;
  if (!Array.isArray(hs) || hs.length < 2) {
    return null;
  }
  const hue = Number(hs[0]);
  const saturation = Number(hs[1]);
  if (!Number.isFinite(hue) || !Number.isFinite(saturation)) {
    return null;
  }

  const brightness =
    typeof state.attributes.brightness === "number"
      ? clamp((state.attributes.brightness / 255) * 100, 0, 100)
      : 100;
  return hsvToRgb(hue, saturation, brightness);
}

export function rgbFromLoxoneValue(value: unknown): RgbColor | null {
  if (typeof value !== "string") {
    return null;
  }
  const match = value.match(HSV_PATTERN);
  if (!match) {
    return null;
  }
  return hsvToRgb(Number(match[1]), Number(match[2]), Number(match[3]));
}

export function formatRgb(rgb: RgbColor): string {
  return `RGB ${rgb.r}, ${rgb.g}, ${rgb.b}`;
}

export function rgbCss(rgb: RgbColor): string {
  return `rgb(${rgb.r}, ${rgb.g}, ${rgb.b})`;
}
