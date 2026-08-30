import { useState, useEffect } from 'react';
import { kbApi } from '../api/kb';
import type { KBDocumentResponse } from '../types';
import { Spinner, Badge, Button, Input, Modal, EmptyState } from '../components/ui';
import { useDebounce } from '../hooks/useDebounce';
import { useToast } from '../hooks/useToast';
import { BookOpen, Search, Upload, FileText, Trash2 } from 'lucide-react';

export function KnowledgeBase() {
  const [docs, setDocs] = useState<KBDocumentResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 500);
  
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState('faq');
  const [uploading, setUploading] = useState(false);
  
  const { toast } = useToast();

  useEffect(() => {
    fetchDocs();
  }, [debouncedSearch]);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      if (debouncedSearch) {
        const hits = await kbApi.search(debouncedSearch);
        setDocs(hits.map((h, i) => ({
          id: `hit-${i}`, 
          title: h.document_title,
          category: 'faq',
          version: h.version,
          source_updated_at: h.source_updated_at,
          content_json: h.text, 
          source_filename: '', content_hash: '', created_at: ''
        } as KBDocumentResponse)));
      } else {
        const res = await kbApi.list();
        setDocs(res);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setUploading(true);
    
    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('category', uploadCategory);

    try {
      await kbApi.upload(formData);
      toast.success('Document uploaded successfully');
      setUploadModalOpen(false);
      setUploadFile(null);
      if (!search) fetchDocs();
    } catch (e: any) {
      toast.error(e.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await kbApi.delete(id);
      toast.success('Document deleted');
      fetchDocs();
    } catch (e: any) {
      toast.error(e.message || 'Failed to delete');
    }
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 shrink-0 animate-fade-in-up">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <div className="w-10 h-10 bg-brand-100 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 rounded-xl flex items-center justify-center">
              <BookOpen size={20} />
            </div>
            <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Knowledge Base</h2>
          </div>
          <p className="text-sm text-slate-500 dark:text-gray-400 mt-1">Manage policies, SOPs, and FAQS used by the AI agent.</p>
        </div>
        
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <Input 
              placeholder="Search documents..." 
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="pl-9 dark:bg-gray-800 dark:border-gray-700 dark:text-white"
            />
          </div>
          <Button onClick={() => setUploadModalOpen(true)} className="shrink-0"><Upload size={16} className="mr-1.5 hidden sm:block" /><span className="sm:hidden">Upload</span><span className="hidden sm:inline">Upload</span></Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {loading ? (
          <div className="flex items-center justify-center h-40"><Spinner size="lg" /></div>
        ) : docs.length === 0 ? (
          <EmptyState icon={FileText} title="No Documents" description={search ? "No matches found for your search." : "Upload documents to train the AI assistant."} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 pb-6 stagger">
            {docs.map(doc => (
              <div key={doc.id} className="card-interactive p-5 flex flex-col">
                <div className="flex justify-between items-start mb-3 gap-4">
                  <h3 className="font-semibold text-slate-900 dark:text-white line-clamp-2">{doc.title}</h3>
                  <Badge variant={
                    doc.category === 'policy' ? 'danger' : 
                    doc.category === 'sop' ? 'warning' : 
                    doc.category === 'faq' ? 'success' : 'info'
                  } className="uppercase shrink-0">{doc.category}</Badge>
                </div>
                
                {search && doc.content_json ? (
                  <div className="text-xs text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-gray-900 p-3 rounded-lg mb-4 italic line-clamp-4 flex-1">
                    "...{doc.content_json}..."
                  </div>
                ) : (
                  <div className="flex-1" />
                )}

                <div className="space-y-2 text-xs mt-4">
                  <div className="flex justify-between">
                    <span className="text-slate-500 dark:text-gray-400 font-medium">Version</span>
                    <span className="font-data font-semibold text-slate-900 dark:text-slate-200">{doc.version}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500 dark:text-gray-400 font-medium">Updated</span>
                    <span className="font-semibold text-slate-900 dark:text-slate-200">{new Date(doc.source_updated_at).toLocaleDateString()}</span>
                  </div>
                </div>

                {!search && (
                  <div className="flex justify-between items-center pt-4 mt-4 border-t border-slate-100 dark:border-gray-700">
                    <span className="text-xs text-slate-400 dark:text-slate-500 font-medium truncate max-w-[150px]">{doc.source_filename}</span>
                    <button onClick={() => handleDelete(doc.id)} className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors">
                      <Trash2 size={16} />
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <Modal open={uploadModalOpen} onClose={() => !uploading && setUploadModalOpen(false)} title="Upload Knowledge Document">
        <form onSubmit={handleUpload} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-gray-400 mb-1.5 uppercase tracking-wide">Category</label>
            <select 
              value={uploadCategory} 
              onChange={e => setUploadCategory(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-slate-800 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-500 transition"
            >
              <option value="faq">FAQ / General Knowledge</option>
              <option value="policy">Company Policy</option>
              <option value="sop">Standard Operating Procedure</option>
              <option value="canned_response">Canned Response</option>
            </select>
          </div>
          <div>
             <label className="block text-xs font-semibold text-slate-600 dark:text-gray-400 mb-1.5 uppercase tracking-wide">Document File</label>
             <input 
               type="file" 
               accept=".pdf,.md,.txt"
               onChange={e => setUploadFile(e.target.files?.[0] || null)}
               className="w-full text-sm text-slate-500 dark:text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100 dark:file:bg-brand-900/30 dark:file:text-brand-400 cursor-pointer"
             />
             <p className="text-[10px] text-slate-400 mt-2 font-medium">Supported formats: PDF, Markdown, TXT. Max size: 10MB.</p>
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-100 dark:border-gray-700">
            <Button type="button" variant="ghost" onClick={() => setUploadModalOpen(false)} disabled={uploading}>Cancel</Button>
            <Button type="submit" loading={uploading} disabled={!uploadFile}>Upload & Index</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
