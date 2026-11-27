import { ago, cigarettesText, hourLabel, levelOf, windowLabel } from "./format";
import { niceTicks } from "./components/HourlyChart";

test("hour labels read naturally", () => {
  expect(hourLabel(0)).toBe("midnight");
  expect(hourLabel(12)).toBe("noon");
  expect(hourLabel(7)).toBe("7 am");
  expect(hourLabel(14)).toBe("2 pm");
  expect(hourLabel(24)).toBe("midnight");
  expect(windowLabel(12, 14)).toBe("noon to 2 pm");
});

test("AQI categories map to four levels", () => {
  expect(levelOf("Good")).toBe("good");
  expect(levelOf("Satisfactory")).toBe("good");
  expect(levelOf("Moderate")).toBe("warning");
  expect(levelOf("Poor")).toBe("serious");
  expect(levelOf("Very Poor")).toBe("critical");
  expect(levelOf("Severe")).toBe("critical");
});

test("cigarette text", () => {
  expect(cigarettesText(0.2)).toBe("less than half a cigarette");
  expect(cigarettesText(1)).toBe("about 1 cigarette");
  expect(cigarettesText(1.64)).toBe("about 1.6 cigarettes");
});

test("ago", () => {
  const now = new Date("2026-11-28T20:00:00");
  expect(ago("2026-11-28T19:40:00", now)).toBe("less than an hour ago");
  expect(ago("2026-11-28T17:00:00", now)).toBe("3 hours ago");
  expect(ago("2026-11-26 20:00:00", now)).toBe("2 days ago");
});

test("chart ticks stay readable", () => {
  expect(niceTicks(66)).toEqual([0, 25, 50]);
  expect(niceTicks(55)).toEqual([0, 10, 20, 30, 40, 50]);
});
