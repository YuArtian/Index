import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  Trash2,
  Upload,
  BookOpen,
  FolderOpen,
  MessageSquare,
} from "lucide-react";
import { progressApi } from "@/api/progress";
import { knowledgeApi } from "@/api/knowledge";

interface LearningItem {
  id: string;
  title: string;
  author: string | null;
  progress: number;
  status: string;
  document_id: string | null;
}

const ACCEPTED_EXTENSIONS = [
  ".txt",
  ".md",
  ".markdown",
  ".pdf",
  ".docx",
  ".csv",
  ".xlsx",
  ".xls",
  ".ipynb",
].join(",");

export default function BookshelfPage() {
  const [items, setItems] = useState<LearningItem[]>([]);
  const [showAdd, setShowAdd] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newAuthor, setNewAuthor] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [highQuality, setHighQuality] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const loadItems = async () => {
    const data = await progressApi.listItems();
    setItems(data.items);
  };

  useEffect(() => {
    loadItems();
  }, []);

  const handleAdd = async () => {
    if (!newTitle.trim()) return;
    setUploading(true);
    try {
      let documentId: string | undefined;

      // Upload file to knowledge base if selected
      if (selectedFile) {
        const res = await knowledgeApi.uploadFile(selectedFile, highQuality);
        documentId = (res as { doc_id?: string })?.doc_id;
      }

      await progressApi.createItem({
        title: newTitle,
        author: newAuthor || undefined,
        document_id: documentId,
      });

      setNewTitle("");
      setNewAuthor("");
      setSelectedFile(null);
      setHighQuality(false);
      setShowAdd(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await loadItems();
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await progressApi.deleteItem(id);
    await loadItems();
  };

  const isPdf = selectedFile?.name.toLowerCase().endsWith(".pdf") ?? false;

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">书架</h1>
            <p className="text-sm text-gray-500 mt-1">导入书籍，边读边问</p>
          </div>
          <button
            onClick={() => setShowAdd(!showAdd)}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus size={16} />
            导入书籍
          </button>
        </div>

        {/* Add book panel */}
        {showAdd && (
          <div className="bg-gray-50 rounded-xl p-5 mb-8 border border-gray-200">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="书名 *"
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                value={newAuthor}
                onChange={(e) => setNewAuthor(e.target.value)}
                placeholder="作者（可选）"
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex items-center gap-3 mb-4">
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_EXTENSIONS}
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0] ?? null;
                  setSelectedFile(file);
                  if (file && !file.name.toLowerCase().endsWith(".pdf"))
                    setHighQuality(false);
                  // Auto-fill title from filename
                  if (file && !newTitle) {
                    setNewTitle(file.name.replace(/\.[^.]+$/, ""));
                  }
                }}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <FolderOpen size={16} className="text-gray-500" />
                {selectedFile ? selectedFile.name : "选择文件（上传到知识库）"}
              </button>
              {isPdf && (
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={highQuality}
                    onChange={(e) => setHighQuality(e.target.checked)}
                    className="w-3.5 h-3.5 accent-blue-600"
                  />
                  <span className="text-xs text-gray-600">高质量 PDF 模式</span>
                </label>
              )}
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleAdd}
                disabled={!newTitle.trim() || uploading}
                className="flex items-center gap-1 px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
              >
                <Upload size={16} />
                {uploading ? "处理中..." : "添加"}
              </button>
              <button
                onClick={() => {
                  setShowAdd(false);
                  setNewTitle("");
                  setNewAuthor("");
                  setSelectedFile(null);
                }}
                className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                取消
              </button>
            </div>
          </div>
        )}

        {/* Book grid */}
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-gray-400">
            <BookOpen size={64} className="mb-4 opacity-40" />
            <p className="text-lg">书架空空如也</p>
            <p className="text-sm mt-1">点击「导入书籍」开始</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5">
            {items.map((item) => (
              <div
                key={item.id}
                onClick={() => navigate(`/read/${item.id}`)}
                className="group relative bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md cursor-pointer transition-all overflow-hidden"
              >
                {/* Book cover placeholder */}
                <div className="aspect-[3/4] bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
                  <div className="text-center">
                    <BookOpen
                      size={32}
                      className="mx-auto mb-2 text-blue-400"
                    />
                    <p className="text-sm font-medium text-gray-700 line-clamp-3">
                      {item.title}
                    </p>
                    {item.author && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-1">
                        {item.author}
                      </p>
                    )}
                  </div>
                </div>

                {/* Progress bar */}
                <div className="px-3 py-2">
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>
                      {item.status === "completed" ? "已完成" : "阅读中"}
                    </span>
                    <span>{item.progress}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all"
                      style={{ width: `${item.progress}%` }}
                    />
                  </div>
                </div>

                {/* Hover actions */}
                <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/chat?book=${item.id}`);
                    }}
                    className="p-1.5 bg-white/90 rounded-lg shadow-sm hover:bg-blue-50 transition-colors"
                    title="提问"
                  >
                    <MessageSquare size={14} className="text-blue-600" />
                  </button>
                  <button
                    onClick={(e) => handleDelete(e, item.id)}
                    className="p-1.5 bg-white/90 rounded-lg shadow-sm hover:bg-red-50 transition-colors"
                    title="删除"
                  >
                    <Trash2 size={14} className="text-red-500" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
