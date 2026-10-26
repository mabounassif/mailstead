import { useEffect, useRef, useState, type ComponentRef } from "react";
import { Animated, Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { slideDecision } from "@/lib/review/queue";
import { colors } from "@/theme";

const THUMB = 44;

type Props = {
  label: string;
  disabled?: boolean;
  reduceMotion: boolean;
  confirmTitle: string;
  confirmBody: string;
  confirmLabel: string;
  onConfirm: () => void;
  onInteractionChange: (active: boolean) => void;
};

export function SlideToConfirm({
  label,
  disabled,
  reduceMotion,
  confirmTitle,
  confirmBody,
  confirmLabel,
  onConfirm,
  onInteractionChange,
}: Props) {
  const [travel, setTravel] = useState(1);
  const [open, setOpen] = useState(false);
  const [focused, setFocused] = useState<"alt" | "cancel" | "confirm" | null>(null);
  const progress = useRef(0);
  const origin = useRef(0);
  const sent = useRef(false);
  const offset = useRef(new Animated.Value(0)).current;
  const confirmRef = useRef<ComponentRef<typeof Pressable>>(null);

  useEffect(() => {
    if (!disabled) {
      sent.current = false;
      progress.current = 0;
      offset.setValue(0);
    }
  }, [disabled, offset]);

  useEffect(() => {
    if (!open) return;
    const node = confirmRef.current as unknown as { focus?: () => void } | null;
    node?.focus?.();
  }, [open]);

  function moveTo(next: number, animate: boolean) {
    const clamped = Math.min(1, Math.max(0, next));
    progress.current = clamped;
    if (animate && !reduceMotion) {
      Animated.timing(offset, { toValue: clamped * travel, duration: 180, useNativeDriver: true }).start();
    } else {
      offset.setValue(clamped * travel);
    }
  }

  function finish() {
    onInteractionChange(false);
    if (!disabled && !sent.current && slideDecision(progress.current) === "commit") {
      sent.current = true;
      moveTo(1, false);
      onConfirm();
      return;
    }
    moveTo(0, true);
  }

  return (
    <View style={styles.wrap}>
      <View
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
        onLayout={(event) => setTravel(Math.max(1, event.nativeEvent.layout.width - THUMB - 8))}
        onStartShouldSetResponder={() => !disabled}
        onMoveShouldSetResponder={() => !disabled}
        onResponderGrant={(event) => {
          if (disabled) return;
          onInteractionChange(true);
          origin.current = event.nativeEvent.pageX - progress.current * travel;
        }}
        onResponderMove={(event) => {
          if (disabled) return;
          moveTo((event.nativeEvent.pageX - origin.current) / travel, false);
        }}
        onResponderRelease={finish}
        onResponderTerminate={finish}
        style={[styles.track, disabled && styles.disabled]}
      >
        <Text style={styles.trackLabel}>{label}</Text>
        <Animated.View style={[styles.thumb, { transform: [{ translateX: offset }] }]} />
      </View>
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Allow this device"
        accessibilityHint="Opens a confirmation step before allowing the device."
        disabled={disabled}
        onPress={() => setOpen(true)}
        onFocus={() => setFocused("alt")}
        onBlur={() => setFocused((current) => (current === "alt" ? null : current))}
        style={[styles.alt, focused === "alt" && styles.focused, disabled && styles.disabled]}
      >
        <Text style={styles.altText}>Allow this device</Text>
      </Pressable>
      <Modal visible={open} transparent animationType={reduceMotion ? "none" : "fade"} onRequestClose={() => setOpen(false)}>
        <View style={styles.backdrop} accessibilityViewIsModal>
          <View style={styles.dialog} accessibilityRole="alert" accessibilityLabel={confirmTitle}>
            <Text style={styles.dialogTitle}>{confirmTitle}</Text>
            <Text style={styles.dialogBody}>{confirmBody}</Text>
            <Pressable
              accessibilityRole="button"
              onPress={() => setOpen(false)}
              onFocus={() => setFocused("cancel")}
              onBlur={() => setFocused((current) => (current === "cancel" ? null : current))}
              style={[styles.dialogQuiet, focused === "cancel" && styles.focused]}
            >
              <Text style={styles.dialogQuietText}>Cancel</Text>
            </Pressable>
            <Pressable
              ref={confirmRef}
              accessibilityRole="button"
              onPress={() => {
                setOpen(false);
                onConfirm();
              }}
              onFocus={() => setFocused("confirm")}
              onBlur={() => setFocused((current) => (current === "confirm" ? null : current))}
              style={[styles.dialogPrimary, focused === "confirm" && styles.focused]}
            >
              <Text style={styles.dialogPrimaryText}>{confirmLabel}</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 8 },
  track: {
    height: 52,
    borderRadius: 26,
    backgroundColor: "#e8f0fe",
    justifyContent: "center",
    overflow: "hidden",
  },
  trackLabel: { textAlign: "center", color: colors.text, fontWeight: "700", fontSize: 15 },
  thumb: {
    position: "absolute",
    left: 4,
    top: 4,
    width: THUMB,
    height: THUMB,
    borderRadius: 22,
    backgroundColor: colors.accent,
  },
  alt: { minHeight: 44, alignItems: "center", justifyContent: "center", borderRadius: 10 },
  altText: { color: colors.accent, fontSize: 15, fontWeight: "600" },
  disabled: { opacity: 0.5 },
  focused: { borderWidth: 2, borderColor: colors.accent },
  backdrop: { flex: 1, backgroundColor: "rgba(32, 33, 36, 0.4)", alignItems: "center", justifyContent: "center", padding: 24 },
  dialog: { width: "100%", maxWidth: 420, backgroundColor: colors.surface, borderRadius: 18, padding: 20, gap: 12 },
  dialogTitle: { color: colors.text, fontSize: 20, fontWeight: "700" },
  dialogBody: { color: colors.text, fontSize: 16, lineHeight: 22 },
  dialogQuiet: { minHeight: 48, borderRadius: 12, borderWidth: 1, borderColor: colors.border, alignItems: "center", justifyContent: "center" },
  dialogQuietText: { color: colors.text, fontWeight: "600", fontSize: 16 },
  dialogPrimary: { minHeight: 48, borderRadius: 12, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center" },
  dialogPrimaryText: { color: "#fff", fontWeight: "700", fontSize: 16 },
});
