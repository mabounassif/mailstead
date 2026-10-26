import { Circle, Line, Path, Rect, Svg } from "react-native-svg";

/** Same Lucide strokes as the desktop workspace rail. */
export type TabIconName = "messages" | "drive" | "contacts" | "settings" | "review";

type Props = {
  name: TabIconName;
  color: string;
  size?: number;
};

const stroke = {
  fill: "none" as const,
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

export function TabIcon({ name, color, size = 22 }: Props) {
  const ink = { ...stroke, stroke: color };
  return (
    <Svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      {name === "messages" ? (
        <Path
          d="M22 17a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 21.286V5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2z"
          {...ink}
        />
      ) : null}
      {name === "drive" ? (
        <>
          <Line x1="22" x2="2" y1="12" y2="12" {...ink} />
          <Path
            d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"
            {...ink}
          />
          <Line x1="6" x2="6.01" y1="16" y2="16" {...ink} />
          <Line x1="10" x2="10.01" y1="16" y2="16" {...ink} />
        </>
      ) : null}
      {name === "contacts" ? (
        <>
          <Path d="M16 2v2" {...ink} />
          <Path d="M7 22v-2a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2" {...ink} />
          <Path d="M8 2v2" {...ink} />
          <Circle cx="12" cy="11" r="3" {...ink} />
          <Rect x="3" y="4" width="18" height="18" rx="2" {...ink} />
        </>
      ) : null}
      {name === "settings" ? (
        <>
          <Path
            d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915"
            {...ink}
          />
          <Circle cx="12" cy="12" r="3" {...ink} />
        </>
      ) : null}
      {name === "review" ? (
        <Path
          fill={color}
          fillRule="evenodd"
          d="M12 1.7 4.1 4.8c-.5.2-.8.7-.8 1.2v6.3c0 4.8 3.5 7.4 8.1 9 .4.2.9.2 1.3 0 4.6-1.6 8.1-4.2 8.1-9V6c0-.5-.3-1-.8-1.2L12 1.7zM12.9 7.1 9.6 12.4H11.9L11 17.1 14.8 11.4H12.5L12.9 7.1z"
        />
      ) : null}
    </Svg>
  );
}
