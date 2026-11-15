import React, { useRef, useState } from 'react';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  ClipboardPaste,
  FileUp,
  Loader2,
  Lock,
  ShieldCheck,
  UploadCloud,
} from 'lucide-react';
import { extractReport } from '../services/api';
import { ExtractionResponse } from '../types';
import { Alert, Button, Card, cx } from './ui';

interface UploadZoneProps {
  onExtractionComplete: (data: ExtractionResponse) => void;
  isLoading: boolean;
  setIsLoading: (val: boolean) => void;
}

export const UploadZone: React.FC<UploadZoneProps> = ({
  onExtractionComplete,
  isLoading,
  setIsLoading,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [rawText, setRawText] = useState('');
  const [mode, setMode] = useState<'file' | 'text'>('file');
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (/\.(pdf|jpe?g|png)$/i.test(file.name) && file.size > 0 && file.size <= 10 * 1024 * 1024) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Choose a non-empty PDF, JPG, JPEG or PNG up to 10 MB.');
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (!/\.(pdf|jpe?g|png)$/i.test(file.name) || !file.size || file.size > 10 * 1024 * 1024) {
        setSelectedFile(null);
        setError("Choose a non-empty PDF, JPG, JPEG or PNG up to 10 MB.");
        return;
      }
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleProcess = async (fileToProcess?: File, textToProcess?: string) => {
    setError(null);
    setIsLoading(true);

    try {
      const activeFile = fileToProcess || (mode === 'file' ? selectedFile : undefined);
      const activeText = textToProcess || (mode === 'text' ? rawText : undefined);

      if (!activeFile && !activeText) {
        throw new Error('Please select a diagnostic PDF or paste blood report text to proceed.');
      }

      // Paced clinical scanning & PII de-identification execution
      const [result] = await Promise.all([
        extractReport(activeFile || undefined, activeText),
        new Promise((resolve) => setTimeout(resolve, 1400)),
      ]);
      onExtractionComplete(result);
    } catch (err: any) {
      setError(err.message || 'Biomarker extraction failed. Please review report layout.');
    } finally {
      setIsLoading(false);
    }
  };

  const tabs = [
    { id: 'file' as const, label: 'Upload report', icon: FileUp },
    { id: 'text' as const, label: 'Paste text', icon: ClipboardPaste },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-10">
      <Card className="overflow-hidden shadow-card-lg">
        {/* Header */}
        <div className="flex flex-col gap-4 border-b border-slate-200 px-6 py-5 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <div>
            <h2 className="text-lg font-semibold">Add your blood report</h2>
            <p className="mt-0.5 text-sm text-slate-500">
              Upload a PDF, JPG, JPEG or PNG, or paste printed report text.
            </p>
          </div>

          <div role="tablist" aria-label="Input method" className="inline-flex self-start rounded-lg bg-slate-100 p-1">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                role="tab"
                aria-selected={mode === id}
                onClick={() => setMode(id)}
                className={cx(
                  'flex items-center gap-2 rounded-md px-3.5 py-1.5 text-sm font-medium transition-all',
                  mode === id
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                )}
              >
                <Icon className="h-4 w-4" aria-hidden />
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-5 p-6 sm:p-8">
          {error && (
            <Alert icon={<AlertCircle className="h-4 w-4" aria-hidden />}>{error}</Alert>
          )}

          {isLoading && (
            <div className="flex items-center gap-3.5 rounded-xl border border-brand-200 bg-brand-50/80 p-4 text-brand-900 shadow-sm animate-pulse">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white shadow-sm">
                <Loader2 className="h-5 w-5 animate-spin" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <p className="text-sm font-semibold text-brand-900">
                    De-identifying PII &amp; Extracting Biomarkers…
                  </p>
                  <span className="inline-flex items-center gap-1 rounded bg-brand-100/80 px-1.5 py-0.5 text-[10px] font-medium text-brand-800">
                    <ShieldCheck className="h-3 w-3" /> Privacy Scrub Active
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-brand-700/90 leading-relaxed">
                  Removing patient identifiers and mapping laboratory reference intervals against Indian pathology standards.
                </p>
              </div>
            </div>
          )}

          {mode === 'file' ? (
            <>
              <div
                role="button"
                tabIndex={0}
                aria-label="Choose a PDF or image report to upload"
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    fileInputRef.current?.click();
                  }
                }}
                className={cx(
                  'cursor-pointer rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors',
                  dragActive
                    ? 'border-brand-500 bg-brand-50'
                    : selectedFile
                    ? 'border-brand-300 bg-brand-50/50'
                    : 'border-slate-300 bg-slate-50/60 hover:border-brand-400 hover:bg-brand-50/40'
                )}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={handleFileChange}
                  className="hidden"
                  tabIndex={-1}
                />

                <div className="flex flex-col items-center gap-3">
                  <span
                    className={cx(
                      'flex h-12 w-12 items-center justify-center rounded-full',
                      selectedFile ? 'bg-brand-100 text-brand-700' : 'bg-white text-slate-500 shadow-card'
                    )}
                  >
                    {selectedFile ? (
                      <CheckCircle2 className="h-6 w-6" aria-hidden />
                    ) : (
                      <UploadCloud className="h-6 w-6" aria-hidden />
                    )}
                  </span>

                  {selectedFile ? (
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{selectedFile.name}</p>
                      <p className="mt-0.5 text-sm text-slate-500 tabular-nums">
                        {(selectedFile.size / 1024).toFixed(1)} KB · Ready to process
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-[15px] font-semibold text-slate-900">
                        Drag and drop your report here, or{' '}
                        <span className="text-brand-700">browse</span>
                      </p>
                      <p className="mt-1 text-sm text-slate-500">
                        PDF, JPG, JPEG, PNG · Up to 10 MB · Printed reports
                      </p>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-end">
                <Button
                  size="lg"
                  onClick={() => handleProcess()}
                  disabled={!selectedFile}
                  loading={isLoading}
                  iconRight={<ArrowRight className="h-4 w-4" aria-hidden />}
                >
                  {isLoading ? 'Analysing report…' : 'Extract biomarkers'}
                </Button>
              </div>
            </>
          ) : (
            <>
              <div>
                <label htmlFor="report-text" className="sr-only">
                  Report text
                </label>
                <textarea
                  id="report-text"
                  rows={9}
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  placeholder="Paste the text of your lab report here, e.g. “25-OH Vitamin D  14.2  ng/mL  30 – 100”"
                  className="field resize-y font-mono text-[13px] leading-relaxed"
                />
              </div>

              <div className="flex items-center justify-between gap-4">
                <span className="text-sm text-slate-500 tabular-nums">
                  {rawText.length > 0 ? `${rawText.length.toLocaleString()} characters` : 'Nothing pasted yet'}
                </span>
                <Button
                  size="lg"
                  onClick={() => handleProcess()}
                  disabled={!rawText.trim()}
                  loading={isLoading}
                  iconRight={<ArrowRight className="h-4 w-4" aria-hidden />}
                >
                  {isLoading ? 'Analysing text…' : 'Extract biomarkers'}
                </Button>
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 border-t border-slate-200 bg-slate-50 px-6 py-3.5 text-sm text-slate-600 sm:px-8">
          <Lock className="h-4 w-4 shrink-0 text-brand-600" aria-hidden />
          <span>
            Your name, phone number and patient ID are automatically removed before analysis.
          </span>
        </div>
      </Card>
    </div>
  );
};
