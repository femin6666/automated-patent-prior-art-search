import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateString: string) {
  try {
    const d = new Date(dateString);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateString;
  }
}

export function getOfficialPatentUrl(patent: { patent_number?: string; title?: string; source_url?: string }): string {
  // If source_url is a real external website (e.g. uspto, arxiv, or already a valid query URL)
  if (
    patent.source_url &&
    patent.source_url.startsWith("http") &&
    !patent.source_url.includes("/patent/US202") &&
    !patent.source_url.includes("/patent/US-202") &&
    !patent.source_url.includes("PAT-CUSTOM")
  ) {
    return patent.source_url;
  }

  // Construct a bulletproof Google Patents query URL using the invention title
  // This format ALWAYS returns HTTP 200 OK on Google Patents without 404 errors
  const searchQuery = patent.title || patent.patent_number || "prior art patent search";
  return `https://patents.google.com/?q=${encodeURIComponent(searchQuery)}`;
}
