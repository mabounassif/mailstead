import { File, Paths } from "expo-file-system";
import { loadSavedInstanceUrl } from "./instanceUrl";
import { loadToken } from "./session";

export async function downloadAuthed(path: string, filename: string): Promise<void> {
  const origin = await loadSavedInstanceUrl();
  const token = await loadToken();
  if (!origin || !token) {
    throw new Error("Sign in again.");
  }
  const safe = filename.replace(/[^A-Za-z0-9._-]+/g, "_").slice(0, 80) || "download";
  const destination = new File(Paths.cache, safe);
  const file = await File.downloadFileAsync(`${origin}${path}`, destination, {
    headers: { Authorization: `Bearer ${token}` },
    idempotent: true,
  });
  if (await File.canPreview(file)) {
    await File.preview(file);
    return;
  }
  throw new Error("The file downloaded, but this device cannot preview it.");
}
