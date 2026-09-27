// src/useI18n.js - React hook wrapper around i18n.js.
// useSyncExternalStore re-renders every component using this hook the moment
// the language changes, wherever that change was triggered from.
import { useSyncExternalStore } from "react";
import { getLang, LANGUAGES, setLang, subscribe, t } from "./i18n";

export function useI18n() {
  const lang = useSyncExternalStore(subscribe, getLang);
  return { lang, setLang, t, LANGUAGES };
}
