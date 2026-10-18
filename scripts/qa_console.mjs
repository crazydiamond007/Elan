/* HTTP LAN origins cannot apply COOP. Record that browser notice without hiding app errors. */
export function recordConsole(message, errors, notices, baseUrl) {
  if (message.type() !== "error") return;
  const text = message.text();
  const origin = new URL(baseUrl);
  if (
    origin.protocol === "http:" &&
    !["localhost", "127.0.0.1", "[::1]"].includes(origin.hostname) &&
    text.startsWith(
      "The Cross-Origin-Opener-Policy header has been ignored, because the URL's origin was untrustworthy.",
    )
  ) {
    if (!notices.includes(text)) notices.push(text);
  } else {
    errors.push(text);
  }
}
