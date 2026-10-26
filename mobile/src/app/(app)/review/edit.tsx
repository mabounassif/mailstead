import { router, useLocalSearchParams } from "expo-router";
import { ScrollView, StyleSheet, Text } from "react-native";
import { Button, TextField } from "@/components/ui";
import { useReview } from "@/lib/review/store";
import { colors } from "@/theme";

export default function EditPreparedMessage() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { items, updateDraft } = useReview();
  const item = items.find((entry) => entry.id === id && entry.draft);
  const draft = item?.draft;

  if (!item || !draft) {
    return (
      <ScrollView contentContainerStyle={styles.pad}>
        <Text style={styles.missing}>This message is no longer waiting for review.</Text>
        <Button label="Back to review" tone="quiet" onPress={() => router.back()} />
      </ScrollView>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.pad} keyboardShouldPersistTaps="handled">
      <Text style={styles.note}>Edits stay on this device. Approving still happens from the review card, and this demo does not send email.</Text>
      <TextField
        label="Name"
        value={draft.toName}
        onChangeText={(toName) => updateDraft(item.id, { ...draft, toName })}
        autoCorrect={false}
      />
      <TextField
        label="Email"
        value={draft.toAddress}
        onChangeText={(toAddress) => updateDraft(item.id, { ...draft, toAddress })}
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="email-address"
      />
      <TextField label="Subject" value={draft.subject} onChangeText={(subject) => updateDraft(item.id, { ...draft, subject })} />
      <TextField
        label="Message"
        value={draft.body}
        onChangeText={(body) => updateDraft(item.id, { ...draft, body })}
        multiline
        style={styles.message}
      />
      <Text style={styles.files}>Attachments</Text>
      {draft.attachments.map((attachment) => (
        <Text key={attachment.id} style={styles.file}>
          {attachment.name}
          {"\n"}
          {attachment.kindLabel} · {attachment.sizeLabel}
          {"\n"}
          {attachment.preview}
        </Text>
      ))}
      <Button label="Back to review" onPress={() => router.back()} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  pad: { padding: 16, gap: 12, paddingBottom: 32 },
  note: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  message: { minHeight: 180, textAlignVertical: "top" },
  files: { color: colors.text, fontWeight: "700", fontSize: 15 },
  file: { color: colors.text, backgroundColor: colors.surface, borderColor: colors.border, borderWidth: 1, borderRadius: 12, padding: 12, lineHeight: 20 },
  missing: { color: colors.text, fontSize: 16 },
});
