import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, X, Loader2, Sparkles } from 'lucide-react';
import { api } from '../config';
import { ParseResumeResponse } from '../types';

interface ResumeImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: (importedData: ParseResumeResponse, category: string) => void;
}

export const ResumeImportModal: React.FC<ResumeImportModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [parsedResult, setParsedResult] = useState<ParseResumeResponse | null>(null);
  const [category, setCategory] = useState<'GENERAL' | 'CUSTOMIZED'>('GENERAL');
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const processFile = async (file: File) => {
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    const validExts = ['.md', '.txt', '.pdf', '.docx'];
    if (!validExts.includes(ext)) {
      setError(`不支持的文件格式 ${ext}。请上传 .md, .txt, .pdf 或 .docx 文件`);
      return;
    }

    setSelectedFile(file);
    setError(null);
    setLoading(true);

    try {
      // For .md and .txt, read directly on client for instant responsiveness
      if (ext === '.md' || ext === '.txt') {
        const text = await file.text();
        const firstLine = text.trim().split('\n')[0] || '';
        const titleClean = firstLine.replace(/^[#\s\-*]+/, '').trim() || file.name.replace(/\.[^/.]+$/, '');
        
        // Extract common tech skills
        const commonSkills = [
          'Python', 'Java', 'C++', 'Go', 'Rust', 'JavaScript', 'TypeScript', 'React', 'Vue',
          'FastAPI', 'Django', 'Spring', 'MySQL', 'PostgreSQL', 'Redis', 'Docker', 'Kubernetes',
          'Git', 'Linux', 'PyTorch', 'TensorFlow', 'LLM', 'AI', 'NLP', 'SQL', 'Flink', 'Kafka'
        ];
        const lowerText = text.toLowerCase();
        const extractedSkills = commonSkills.filter(s => lowerText.includes(s.toLowerCase()));

        setParsedResult({
          title: titleClean,
          content_markdown: text,
          skills: extractedSkills,
          filename: file.name,
          file_size: file.size
        });
      } else {
        // Use backend parse endpoint for binary files (.pdf, .docx)
        const formData = new FormData();
        formData.append('file', file);
        const res = await api.post('/api/resumes/parse-file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        setParsedResult({
          title: res.data.title,
          content_markdown: res.data.content_markdown,
          skills: res.data.skills || [],
          filename: file.name,
          file_size: file.size
        });
      }
    } catch (err: any) {
      console.error('Parse resume error', err);
      setError(err?.response?.data?.detail || '解析文件失败，请检查文件格式或后端服务');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleConfirm = () => {
    if (parsedResult) {
      onImportSuccess(parsedResult, category);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 animate-fadeIn">
      <div className="bg-[#11131c] border border-[#24283b] w-full max-w-xl rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="p-5 border-b border-[#24283b] flex items-center justify-between bg-[#151824]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-cyan-600/20 text-cyan-400 rounded-xl border border-cyan-500/30">
              <Upload className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[#f3f4f6]">导入简历文件</h3>
              <p className="text-[11px] text-[#9ca3af]">支持 .md / .txt / .pdf / .docx，自动提取 Markdown 与技能画像</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-[#9ca3af] hover:text-[#f3f4f6] hover:bg-[#1b1e2e] rounded-lg transition"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-950/40 border border-rose-500/30 rounded-xl flex items-center gap-2 text-xs text-rose-400">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Upload Dropzone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
              dragActive
                ? 'border-cyan-500 bg-cyan-950/20'
                : 'border-[#24283b] hover:border-cyan-500/50 bg-[#0e1017]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".md,.txt,.pdf,.docx"
              onChange={handleChange}
              className="hidden"
            />
            {loading ? (
              <div className="flex flex-col items-center justify-center space-y-2 py-4">
                <Loader2 className="h-8 w-8 text-cyan-400 animate-spin" />
                <span className="text-xs text-[#d1d5db] font-medium">正在解析简历结构与技能标签...</span>
              </div>
            ) : selectedFile ? (
              <div className="flex flex-col items-center justify-center space-y-2 py-2">
                <div className="p-3 bg-emerald-950/40 text-emerald-400 border border-emerald-500/30 rounded-2xl">
                  <FileText className="h-7 w-7" />
                </div>
                <span className="text-xs font-bold text-[#f3f4f6]">{selectedFile.name}</span>
                <span className="text-[10px] text-[#6b7280] font-mono">
                  {(selectedFile.size / 1024).toFixed(1)} KB · 点击可重新选择文件
                </span>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center space-y-3 py-2">
                <div className="p-3 bg-cyan-600/10 text-cyan-400 border border-cyan-500/20 rounded-2xl">
                  <Upload className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#f3f4f6]">
                    拖拽简历文件到此处，或 <span className="text-cyan-400 hover:underline">点击浏览文件</span>
                  </p>
                  <p className="text-[10px] text-[#6b7280] mt-1">单文件大小建议不超过 10MB</p>
                </div>
              </div>
            )}
          </div>

          {/* Parsed Result Preview Card */}
          {parsedResult && (
            <div className="p-4 bg-[#151824] border border-[#24283b] rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs font-bold text-[#f3f4f6]">已识别标题: {parsedResult.title}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <label className="text-[11px] text-[#9ca3af]">版本归类:</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value as any)}
                    className="bg-[#0e1017] border border-[#24283b] text-xs text-[#f3f4f6] rounded-lg px-2 py-1 outline-none focus:border-cyan-500"
                  >
                    <option value="GENERAL">通用基准简历</option>
                    <option value="CUSTOMIZED">专岗定制版本</option>
                  </select>
                </div>
              </div>

              {parsedResult.skills && parsedResult.skills.length > 0 && (
                <div>
                  <span className="text-[10px] text-[#9ca3af] flex items-center gap-1 mb-1.5">
                    <Sparkles className="h-3 w-3 text-cyan-400" /> 识别到技术技能 ({parsedResult.skills.length} 项):
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {parsedResult.skills.map((s, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] bg-cyan-950/50 text-cyan-300 border border-cyan-500/30 px-2 py-0.5 rounded font-mono"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-[11px] text-[#9ca3af] bg-[#0e1017] p-2.5 rounded-lg border border-[#24283b] max-h-24 overflow-y-auto font-mono line-clamp-3">
                {parsedResult.content_markdown.substring(0, 200)}...
              </div>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[#24283b] bg-[#151824] flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs text-[#9ca3af] hover:text-[#f3f4f6] hover:bg-[#1b1e2e] rounded-xl transition"
          >
            取消
          </button>
          <button
            disabled={!parsedResult || loading}
            onClick={handleConfirm}
            className="px-5 py-2 text-xs font-semibold text-white bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl shadow-md shadow-cyan-900/40 transition"
          >
            导入并进入工作台
          </button>
        </div>
      </div>
    </div>
  );
};
