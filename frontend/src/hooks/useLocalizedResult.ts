import { useEffect, useState } from 'react';
import { useLanguage } from '../lib/i18n';
import { localizeAnalysis } from '../services/api';
import { FullAnalysisResponse } from '../types';

/** The analysis in the chosen language (English is shown until the translation arrives, or if it fails). */
export function useLocalizedResult(result: FullAnalysisResponse): FullAnalysisResponse {
  const language = useLanguage();
  const [shown, setShown] = useState(result);
  useEffect(() => {
    let alive = true;
    if (language === 'en') {
      setShown(result);
      return;
    }
    localizeAnalysis(result, language)
      .then((r) => alive && setShown({ ...r, saved_to_history: result.saved_to_history, diet_plan: result.diet_plan }))
      .catch(() => alive && setShown(result));
    return () => {
      alive = false;
    };
  }, [result, language]);
  return shown;
}
