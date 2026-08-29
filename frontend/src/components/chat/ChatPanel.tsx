import { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { chatApi } from '../../api/chat';
import type { ChatMessage as APIChatMessage } from '../../types';
import { Send, Bot, Check, ChevronDown } from 'lucide-react';
import { Button, Spinner } from '../ui';
import { useToast } from '../../hooks/useToast';

interface UIChatMessage extends APIChatMessage {
  id: string;
  fromUser: boolean;
}

export function ChatPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<UIChatMessage[]>([
    { 
      id: 'welcome', fromUser: false, type: 'text', 
      content: 'Hi! I am OpsAssist AI. I can help you find documentation, check order status, or update tickets. How can I help?', 
      action_diff: null, pending_action: null, citations: null, status: 'final', 
      resolved_entity_id: null, resolved_entity_type: null 
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [confirmingMap, setConfirmingMap] = useState<Record<string, boolean>>({});
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const { toast } = useToast();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  const getActiveContext = () => {
    const path = location.pathname;
    if (path.startsWith('/customers/')) return { type: 'customer', id: path.split('/')[2] };
    if (path.startsWith('/tickets/')) return { type: 'ticket', id: path.split('/')[2] };
    return { type: null, id: null };
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userText = input.trim();
    setInput('');
    
    const newUserMsg: UIChatMessage = {
      id: Date.now().toString(),
      fromUser: true,
      type: 'text',
      content: userText,
      action_diff: null, pending_action: null, citations: null, status: 'final',
      resolved_entity_id: null, resolved_entity_type: null
    };
    
    setMessages(prev => [...prev, newUserMsg]);
    setLoading(true);

    try {
      const ctx = getActiveContext();
      const res = await chatApi.send(userText, ctx.id, ctx.type);
      
      if (res.messages && res.messages.length > 0) {
        const aiReply = res.messages[res.messages.length - 1];
        setMessages(prev => [...prev, { ...aiReply, id: (Date.now() + 1).toString(), fromUser: false }]);
      }
    } catch (e: any) {
      toast.error('Failed to send message');
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        fromUser: false,
        type: 'error',
        content: e.message || 'An error occurred while connecting to the AI agent.',
        action_diff: null, pending_action: null, citations: null, status: 'final',
        resolved_entity_id: null, resolved_entity_type: null
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (token: string, msgId: string) => {
    setConfirmingMap(prev => ({ ...prev, [token]: true }));
    try {
      const res = await chatApi.confirm(token);
      toast.success(res.message);
      setMessages(prev => prev.map(m => m.id === msgId ? { ...m, status: 'final' } : m));
    } catch (e: any) {
      toast.error(e.message || 'Action failed');
    } finally {
      setConfirmingMap(prev => ({ ...prev, [token]: false }));
    }
  };

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-brand-600 text-white rounded-full shadow-lg shadow-brand-500/30 hover:bg-brand-700 hover:scale-105 transition-all flex items-center justify-center z-50 group"
      >
        <Bot size={24} className="group-hover:animate-bounce" />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-[calc(100%-3rem)] sm:w-[380px] h-[600px] max-h-[calc(100vh-6rem)] bg-white dark:bg-gray-800 rounded-2xl shadow-2xl shadow-slate-900/10 border border-slate-200 dark:border-gray-700 flex flex-col z-50 overflow-hidden transform origin-bottom-right transition-all">
      <div className="p-4 bg-brand-600 text-white flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <Bot size={20} />
          <h3 className="font-semibold text-[15px]">OpsAssist AI</h3>
        </div>
        <button onClick={() => setIsOpen(false)} className="text-white/80 hover:text-white hover:bg-white/20 p-1.5 rounded-lg transition">
          <ChevronDown size={20} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5 bg-slate-50 dark:bg-gray-900/50 scrollbar-thin">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.fromUser ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] rounded-2xl p-3.5 text-[13px] leading-relaxed ${
              msg.fromUser 
                ? 'bg-brand-600 text-white rounded-tr-sm shadow-sm' 
                : 'bg-white dark:bg-gray-800 border border-slate-200 dark:border-gray-700 text-slate-800 dark:text-slate-200 rounded-tl-sm shadow-sm'
            }`}>
              <div className="whitespace-pre-wrap">{msg.content}</div>
              
              {!msg.fromUser && msg.type === 'action-confirmation' && msg.pending_action && (
                <div className="mt-4 p-3 bg-brand-50/50 dark:bg-brand-900/10 border border-brand-100 dark:border-brand-800/40 rounded-xl">
                  <div className="font-semibold text-[11px] text-brand-800 dark:text-brand-400 mb-2.5 uppercase tracking-wider">Review Action</div>
                  
                  {msg.action_diff && (
                    <div className="mb-3 text-xs flex gap-2 items-center bg-white dark:bg-gray-900 p-2.5 rounded-lg border border-slate-100 dark:border-gray-700 shadow-sm">
                       <span className="text-red-500 line-through truncate flex-1 opacity-75">{String(Object.values(msg.action_diff.before)[0] || 'Empty')}</span>
                       <span className="text-slate-400 shrink-0">?</span>
                       <span className="text-emerald-600 dark:text-emerald-400 font-medium truncate flex-1">{String(Object.values(msg.action_diff.after)[0] || 'Empty')}</span>
                    </div>
                  )}

                  {msg.status === 'pending_confirmation' ? (
                    <Button 
                      size="sm" 
                      loading={confirmingMap[msg.pending_action.token]} 
                      onClick={() => handleConfirm(msg.pending_action!.token, msg.id)}
                      className="w-full text-xs py-2 shadow-sm shadow-brand-500/20"
                    >
                      Authorize Action
                    </Button>
                  ) : (
                    <div className="flex items-center justify-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 px-3 py-2 rounded-lg border border-emerald-100 dark:border-emerald-900/40">
                      <Check size={14} strokeWidth={3} /> Action Executed
                    </div>
                  )}
                </div>
              )}

              {!msg.fromUser && msg.type === 'citation-answer' && msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100 dark:border-gray-700">
                  <div className="text-[10px] text-slate-500 dark:text-gray-400 font-bold mb-1.5 uppercase tracking-wider">Sources Consulted</div>
                  <div className="space-y-1">
                    {msg.citations.map((cit, idx) => (
                      <div key={idx} className="text-xs text-brand-600 dark:text-brand-400 truncate hover:underline cursor-pointer flex items-center gap-1.5">
                        <span className="opacity-50">[{idx + 1}]</span> {cit.document_title} <span className="opacity-50 text-[10px]">(v{cit.version})</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white dark:bg-gray-800 border border-slate-200 dark:border-gray-700 rounded-2xl rounded-tl-sm p-4 shadow-sm flex items-center gap-2">
              <Spinner size="sm" className="opacity-50" />
              <span className="text-xs text-slate-400 font-medium">OpsAssist is thinking...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-3 bg-white dark:bg-gray-800 border-t border-slate-200 dark:border-gray-700 shrink-0">
        <form 
          onSubmit={e => { e.preventDefault(); handleSend(); }}
          className="flex items-center gap-2"
        >
          <input 
            type="text" 
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Type your message..." 
            className="flex-1 bg-slate-100 dark:bg-gray-900 border-transparent focus:bg-white dark:focus:bg-gray-800 focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 rounded-xl px-4 py-2.5 text-[13px] outline-none transition-all dark:text-white placeholder:text-slate-400"
          />
          <button 
            type="submit"
            disabled={!input.trim() || loading}
            className="w-10 h-10 rounded-xl bg-brand-600 text-white flex items-center justify-center hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed shrink-0 transition-colors shadow-sm shadow-brand-500/20"
          >
            <Send size={16} className="ml-0.5" />
          </button>
        </form>
      </div>
    </div>
  );
}
