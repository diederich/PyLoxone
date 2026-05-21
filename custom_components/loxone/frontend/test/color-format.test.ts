import { describe, expect, it } from "vitest";
import {
  formatRgb,
  hsvToRgb,
  rgbFromHassState,
  rgbFromLoxoneValue,
} from "../src/color-format";
import type { HassState } from "../src/types";

function hassState(attributes: Record<string, unknown>, state = "on"): HassState {
  return {
    entity_id: "light.test",
    state,
    attributes,
  };
}

describe("color-format", () => {
  it("formats RGB values", () => {
    expect(formatRgb({ r: 1, g: 2, b: 3 })).toBe("RGB 1, 2, 3");
  });

  it("converts HSV values to RGB", () => {
    expect(hsvToRgb(0, 100, 100)).toEqual({ r: 255, g: 0, b: 0 });
    expect(hsvToRgb(120, 100, 50)).toEqual({ r: 0, g: 128, b: 0 });
    expect(hsvToRgb(240, 100, 100)).toEqual({ r: 0, g: 0, b: 255 });
  });

  it("uses HA rgb_color when available", () => {
    expect(rgbFromHassState(hassState({ rgb_color: [260, 20.2, -5] }))).toEqual({
      r: 255,
      g: 20,
      b: 0,
    });
  });

  it("falls back to HA hs_color and brightness", () => {
    expect(
      rgbFromHassState(
        hassState({
          hs_color: [60, 100],
          brightness: 128,
        }),
      ),
    ).toEqual({ r: 128, g: 128, b: 0 });
  });

  it("keeps HA color attributes visible while the light is off", () => {
    expect(rgbFromHassState(hassState({ rgb_color: [255, 0, 0] }, "off"))).toEqual({
      r: 255,
      g: 0,
      b: 0,
    });
  });

  it("ignores unavailable or non-color HA states", () => {
    expect(rgbFromHassState(hassState({ rgb_color: [255, 0, 0] }, "unavailable"))).toBeNull();
    expect(rgbFromHassState(hassState({ brightness: 255 }))).toBeNull();
    expect(rgbFromHassState(undefined)).toBeNull();
  });

  it("parses Loxone hsv runtime strings", () => {
    expect(rgbFromLoxoneValue("hsv(180,100,50)")).toEqual({ r: 0, g: 128, b: 128 });
    expect(rgbFromLoxoneValue("hsv( 300.0, 50, 100 )")).toEqual({
      r: 255,
      g: 128,
      b: 255,
    });
  });

  it("ignores unsupported Loxone runtime values", () => {
    expect(rgbFromLoxoneValue("temp(50,3000)")).toBeNull();
    expect(rgbFromLoxoneValue("On")).toBeNull();
    expect(rgbFromLoxoneValue(["hsv(0,100,100)"])).toBeNull();
  });
});
