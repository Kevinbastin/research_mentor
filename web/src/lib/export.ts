import TurndownService from "turndown";
import { generateHTML } from "@tiptap/html";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";

export const extensions = [StarterKit, Image];

export function tiptapJsonToHtml(json: any) {
  try {
    return generateHTML(json, extensions);
  } catch (e) {
    console.error("Failed to convert to HTML", e);
    return "";
  }
}

export function tiptapJsonToMarkdown(json: any) {
  const html = tiptapJsonToHtml(json);
  const turndown = new TurndownService({ headingStyle: "atx" });
  return turndown.turndown(html);
}
