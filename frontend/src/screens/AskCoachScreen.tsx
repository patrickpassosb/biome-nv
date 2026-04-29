import { useState, useRef, useEffect } from 'react';
import { api } from '../api';
import { Bot, Utensils, Dumbbell, BarChart3, Bed, ArrowUp, Paperclip } from 'lucide-react';
import { useUser } from '../contexts/UserContext';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const suggestions = [
  { icon: Utensils, title: 'Adjust Macros', subtitle: 'Recalculate for rest day', question: 'Should I adjust my macros for a rest day?' },
  { icon: Dumbbell, title: 'Swap Exercise', subtitle: 'Alternative for squats', question: 'What is a good alternative exercise for squats?' },
  { icon: BarChart3, title: 'Analyze Volume', subtitle: 'Am I doing too much chest?', question: 'Am I doing too much chest volume?' },
  { icon: Bed, title: 'Recovery Status', subtitle: 'Should I train today?', question: 'Based on my recent data, should I train today?' },
];

export default function AskCoachScreen() {
  const { activeUser } = useUser();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  async function send(text: string) {
    if (!text.trim() || loading) return;
    const userMsg: Message = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await api.chat(text, activeUser?.id);
      setMessages(prev => [...prev, { role: 'assistant', content: res.reply }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I had trouble connecting. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  }

  const hasMessages = messages.length > 0;

  return (
    <div className="flex flex-col h-[calc(100vh-6rem)]">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white">Ask Coach</h1>
        <p className="text-on-surface-variant mt-1">Ask anything about your training</p>
      </div>

      {!hasMessages ? (
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="w-16 h-16 rounded-full bg-surface-container border border-border flex items-center justify-center mb-4">
            <Bot className="w-8 h-8 text-primary-container" />
          </div>
          <h2 className="text-xl font-medium text-white mb-8">Ask me anything</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-[600px]">
            {suggestions.map((s) => (
              <button
                key={s.title}
                onClick={() => send(s.question)}
                className="bg-surface-container border border-border hover:border-primary-container transition-colors rounded-lg p-4 text-left flex items-start gap-4 group"
              >
                <s.icon className="w-5 h-5 text-on-surface-variant group-hover:text-primary-container transition-colors mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-white">{s.title}</p>
                  <p className="text-xs text-on-surface-variant mt-0.5">{s.subtitle}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-6 pr-2">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {m.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-surface-container border border-border flex items-center justify-center shrink-0 mr-3">
                  <Bot className="w-4 h-4 text-primary-container" />
                </div>
              )}
              <div className={`max-w-[75%] ${m.role === 'user' ? 'bg-surface-container rounded-xl rounded-tr-sm border border-border p-4' : 'pt-1'}`}>
                {m.role === 'assistant' && <span className="text-[11px] uppercase tracking-wider text-on-surface-variant mb-1 block">Biome</span>}
                <p className="text-sm text-on-surface whitespace-pre-wrap">{m.content}</p>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="w-8 h-8 rounded-full bg-surface-container border border-border flex items-center justify-center shrink-0 mr-3">
                <Bot className="w-4 h-4 text-primary-container" />
              </div>
              <div className="flex gap-1 items-center h-8">
                <span className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-on-surface-variant rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-border">
        <div className="max-w-[800px] mx-auto relative flex items-center">
          <button className="absolute left-3 text-on-surface-variant hover:text-white transition-colors">
            <Paperclip className="w-5 h-5" />
          </button>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send(input)}
            placeholder="Ask Biome anything..."
            className="w-full bg-background border border-border focus:border-primary-container focus:outline-none rounded-full py-3 pl-12 pr-12 text-sm text-white placeholder:text-on-surface-variant/50"
          />
          <button
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
            className="absolute right-2 h-8 w-8 bg-primary-container rounded-full flex items-center justify-center text-on-primary hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </div>
        <p className="text-center mt-3 text-[10px] text-on-surface-variant/50 uppercase tracking-widest">
          AI CAN MAKE MISTAKES. VERIFY IMPORTANT TRAINING ADVICE.
        </p>
      </div>
    </div>
  );
}
