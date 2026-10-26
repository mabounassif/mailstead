/** Chat list stays in the tab bar. An open conversation covers it. */
export function messageChatCoversTabs(pathname: string): boolean {
  const path = pathname.split("?")[0].replace(/\/+$/, "") || "/";
  return path.startsWith("/messages/");
}
