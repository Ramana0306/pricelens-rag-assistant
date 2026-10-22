import { useEffect, useRef, useState } from 'react'
import { ArrowDownRight, ArrowRight, BookOpenText, Check, ChevronRight, CircleHelp, FileText, Globe2, Link2, LoaderCircle, MessageCircle, Plus, Send, ShieldCheck, Sparkles, Upload, X } from 'lucide-react'
import { analyzeProduct, askQuestion, ingestText } from './lib/api'

const suggestions = [
  'What are the main features?',
  'What is the warranty period?',
  'Does it support fast charging?',
  'Summarize the specifications',
]

function App() {
  const [url, setUrl] = useState('')
  const [product, setProduct] = useState(null)
  const [comparisonId, setComparisonId] = useState(null)
  const [notice, setNotice] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [question, setQuestion] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const [showManual, setShowManual] = useState(false)
  const [manualText, setManualText] = useState('')
  const [manualTitle, setManualTitle] = useState('Product notes')
  const [sourcesOpen, setSourcesOpen] = useState({})
  const chatEnd = useRef(null)

  useEffect(() => { chatEnd.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, chatLoading])

  async function handleAnalyze(e) {
    e?.preventDefault()
    if (!url.trim() || loading) return
    setLoading(true); setError(''); setNotice(''); setProduct(null); setMessages([]); setComparisonId(null)
    try {
      const result = await analyzeProduct(url.trim())
      setProduct(result.product); setComparisonId(result.comparison_id); setNotice(result.notice || '')
      setMessages([{ role: 'assistant', content: `I've processed the information I could extract for ${result.product?.name || 'this product'}. Ask me a question and I'll search the saved product notes for relevant evidence.`, sources: result.sources || [] }])
    } catch (err) { setError(err.message || 'Unable to read this product page.') }
    finally { setLoading(false) }
  }

  async function handleManual(e) {
    e?.preventDefault()
    if (manualText.trim().length < 30 || loading) return
    setLoading(true); setError(''); setNotice('')
    try {
      const result = await ingestText({ title: manualTitle || 'Product notes', content: manualText, source_url: url || '' })
      setProduct(result.product); setComparisonId(result.comparison_id); setNotice(result.notice || 'Your product notes were saved for this guest session.')
      setMessages([{ role: 'assistant', content: `I've saved your notes for ${result.product?.name || 'this product'}. Ask a question about the information you provided.`, sources: result.sources || [] }])
      setShowManual(false); setManualText('')
    } catch (err) { setError(err.message || 'Unable to save product notes.') }
    finally { setLoading(false) }
  }

  async function sendQuestion(text = question) {
    const q = text.trim()
    if (!q || chatLoading || !comparisonId) return
    setQuestion(''); setMessages(m => [...m, { role: 'user', content: q }]); setChatLoading(true)
    try {
      const result = await askQuestion(q, comparisonId)
      setMessages(m => [...m, { role: 'assistant', content: result.answer, sources: result.sources || [] }])
    } catch (err) { setMessages(m => [...m, { role: 'assistant', content: `I couldn't get an answer: ${err.message}` }]) }
    finally { setChatLoading(false) }
  }

  function resetWorkspace() {
    setUrl(''); setProduct(null); setComparisonId(null); setNotice(''); setError(''); setMessages([]); setQuestion(''); setShowManual(false)
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <button className="brand" onClick={resetWorkspace} aria-label="PriceLens AI home"><span className="brand-mark"><Sparkles size={20}/></span><span className="brand-copy"><b>PriceLens <i>AI</i></b><small>PRODUCT KNOWLEDGE, MADE SIMPLE</small></span></button>
      <div className="sidebar-label">WORKSPACE</div>
      <button className="side-link selected"><BookOpenText size={17}/> Product assistant <span className="side-active"/></button>
      <button className="side-link" onClick={() => setShowManual(true)}><FileText size={17}/> Add product notes</button>
      <div className="side-rule"/>
      <div className="sidebar-label">HOW IT WORKS</div>
      <div className="side-explainer"><span>01</span><div><b>Add a product</b><p>Paste a public product URL or add text manually.</p></div></div>
      <div className="side-explainer"><span>02</span><div><b>Build knowledge</b><p>Product text is split into chunks and saved for retrieval.</p></div></div>
      <div className="side-explainer"><span>03</span><div><b>Ask anything</b><p>Get answers grounded in the saved product information.</p></div></div>
      <div className="sidebar-bottom"><div className="privacy-card"><ShieldCheck size={19}/><div><b>No account required</b><p>Start instantly with a temporary guest workspace.</p></div></div><div className="guest-status"><span className="status-dot"/> Guest workspace <span className="guest-badge">PRIVATE</span></div></div>
    </aside>

    <main className="main-content">
      <header className="topbar"><div className="crumb"><span>Workspace</span><ChevronRight size={14}/><b>Product assistant</b></div><div className="top-right"><span className="secure-label"><ShieldCheck size={15}/> No login needed</span><button className="help-button" title="How it works" onClick={() => document.getElementById('workflow')?.scrollIntoView({ behavior: 'smooth' })}><CircleHelp size={18}/></button></div></header>
      <div className="content-wrap">
        <section className="hero">
          <div className="hero-copy"><div className="eyebrow"><span className="eyebrow-spark"><Sparkles size={13}/></span> YOUR PERSONAL PRODUCT EXPERT</div><h1>Know what you're<br/><span>buying, before you buy.</span></h1><p>Drop in a product link. PriceLens reads the available details and turns them into a searchable knowledge base you can ask questions about.</p><div className="hero-points"><span><Check size={14}/> No registration</span><span><Check size={14}/> Evidence-based answers</span><span><Check size={14}/> Sources included</span></div></div>
          <div className="hero-art" aria-hidden="true"><div className="art-orbit orbit-a"/><div className="art-orbit orbit-b"/><div className="art-core"><div className="art-page"><div className="art-page-top"><span/><span/><span/></div><div className="art-lines"><i/><i/><i/><i/></div><div className="art-check"><Check size={23}/></div></div><div className="art-star star-a"><Sparkles size={17}/></div><div className="art-star star-b"><MessageCircle size={18}/></div><div className="art-tag">RAG <span>READY</span></div></div></div>
        </section>

        <section className="ingest-card">
          <div className="card-heading"><div className="card-icon"><Link2 size={19}/></div><div><h2>Start with a product link</h2><p>We'll extract accessible page text, chunk it, and store it for question answering.</p></div><span className="step-pill">STEP 01</span></div>
          <form className="url-form" onSubmit={handleAnalyze}><label className="url-field"><Globe2 size={18}/><input value={url} onChange={e => setUrl(e.target.value)} placeholder="Paste a product page URL (Amazon, Flipkart, brand site…)" aria-label="Product URL"/><button type="button" className="clear-url" onClick={() => setUrl('')} aria-label="Clear URL">{url && <X size={16}/>}</button></label><button className="primary-button" type="submit" disabled={loading || !url.trim()}>{loading ? <><LoaderCircle size={17} className="spin"/> Reading page</> : <>Build knowledge <ArrowRight size={17}/></>}</button></form>
          <div className="ingest-bottom"><div className="site-note"><span className="mini-globe"><Globe2 size={13}/></span> Works with accessible public product pages</div><button className="manual-link" onClick={() => setShowManual(v => !v)}><Plus size={15}/> Add text manually instead</button></div>
          {error && <div className="error-banner"><X size={16}/><span>{error}</span></div>}
          {notice && <div className="notice-banner"><ShieldCheck size={16}/><span>{notice}</span></div>}
        </section>

        {showManual && <section className="manual-card"><div className="manual-head"><div><h3><FileText size={18}/> Add product information manually</h3><p>Useful when a retailer blocks automated page extraction. Paste specifications, manual text, or warranty details.</p></div><button className="icon-close" onClick={() => setShowManual(false)} aria-label="Close"><X size={18}/></button></div><form onSubmit={handleManual} className="manual-form"><input value={manualTitle} onChange={e => setManualTitle(e.target.value)} placeholder="Product title" aria-label="Product title"/><textarea value={manualText} onChange={e => setManualText(e.target.value)} placeholder="Paste product description, features, specifications, warranty terms… (at least 30 characters)" rows={5}/><div className="manual-actions"><span>{manualText.length} characters</span><button className="primary-button" type="submit" disabled={loading || manualText.trim().length < 30}>{loading ? <LoaderCircle className="spin" size={16}/> : <Upload size={16}/>} Save knowledge</button></div></form></section>}

        <div className="workspace-grid">
          <section className="product-panel panel-card">
            <div className="panel-heading"><div><div className="panel-kicker">YOUR KNOWLEDGE BASE</div><h2>Product details</h2></div><span className={product ? 'status-pill ready' : 'status-pill'}><span/> {product ? 'Ready' : 'Awaiting link'}</span></div>
            {!product ? <div className="product-empty"><div className="empty-icon"><FileText size={26}/><span><Plus size={13}/></span></div><h3>Your product will appear here</h3><p>After extraction, we'll show the title, source, and how many text chunks were saved.</p><div className="empty-divider"/><div className="mini-step"><span>1</span> Paste a product URL above</div><div className="mini-step"><span>2</span> Extract page text and save chunks</div><div className="mini-step"><span>3</span> Ask questions in the assistant</div></div> : <div className="product-details"><div className="product-icon"><BookOpenText size={27}/></div><div className="product-title"><h3>{product.name || 'Product information'}</h3><p>{product.brand && product.brand !== 'Unknown' ? `${product.brand} · ` : ''}{product.source_url || url}</p></div><div className="product-meta"><div><span>CONTENT</span><b>{product.character_count ? `${product.character_count.toLocaleString()} chars` : 'Saved'}</b></div><div><span>CHUNKS</span><b>{product.chunk_count ?? '—'}</b></div><div><span>SOURCE</span><b>{product.source_type || 'Product URL'}</b></div></div>{product.description && <p className="product-description">{product.description}</p>}{Array.isArray(product.highlights) && product.highlights.length > 0 && <div className="highlights"><b>Extracted highlights</b>{product.highlights.slice(0, 5).map((h, i) => <div key={i}><Check size={14}/>{h}</div>)}</div>}</div>}
            <div className="panel-footer"><ShieldCheck size={15}/><span>Answers are limited to the information successfully extracted or added.</span></div>
          </section>

          <section className="chat-panel panel-card" id="assistant">
            <div className="chat-heading"><div className="ai-avatar"><Sparkles size={19}/></div><div><h2>Ask your product</h2><p><span className={product ? 'online-dot' : 'offline-dot'}/>{product ? 'Knowledge base connected' : 'Add a product to start chatting'}</p></div><span className="ai-chip">AI ASSISTANT</span></div>
            <div className="chat-body">
              {!messages.length ? <div className="chat-welcome"><div className="welcome-icon"><MessageCircle size={25}/></div><h3>Your product, explained.</h3><p>Ask about features, compatibility, specifications, warranty, or anything else covered in the product information.</p><div className="suggestion-grid">{suggestions.map((s, i) => <button key={s} onClick={() => sendQuestion(s)} disabled={!product || chatLoading}><span>{['✦', '◈', '↗', '≡'][i]}</span>{s}<ArrowDownRight size={14}/></button>)}</div></div> : <div className="messages">{messages.map((m, i) => <div key={i} className={`message-row ${m.role}`}><div className="message-avatar">{m.role === 'assistant' ? <Sparkles size={15}/> : 'You'}</div><div className="message-content"><div className="message-bubble">{m.content}</div>{m.sources?.length > 0 && <div className="source-area"><button className="source-toggle" onClick={() => setSourcesOpen(s => ({...s, [i]: !s[i]}))}><BookOpenText size={14}/> {m.sources.length} source{m.sources.length > 1 ? 's' : ''} <ChevronRight size={13} className={sourcesOpen[i] ? 'rotated' : ''}/></button>{sourcesOpen[i] && <div className="source-list">{m.sources.map((source, j) => <div key={j} className="source-item"><b>{source.label || `Source ${j + 1}`}</b><span>{source.topic || 'Product information'}</span>{source.url && <a href={source.url} target="_blank" rel="noreferrer">Open source <ArrowRight size={12}/></a>}</div>)}</div>}</div>}</div></div>)}{chatLoading && <div className="message-row assistant"><div className="message-avatar"><Sparkles size={15}/></div><div className="typing"><i/><i/><i/> Searching product knowledge</div></div>}<div ref={chatEnd}/></div>}
            </div>
            <div className="chat-compose"><form onSubmit={e => { e.preventDefault(); sendQuestion() }}><textarea value={question} onChange={e => setQuestion(e.target.value)} placeholder={product ? 'Ask a question about this product…' : 'Add a product first to enable questions'} rows={1} disabled={!product || chatLoading} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuestion() } }}/><button type="submit" disabled={!product || !question.trim() || chatLoading} aria-label="Send question">{chatLoading ? <LoaderCircle className="spin" size={17}/> : <Send size={17}/>}</button></form><div className="compose-foot"><span><ShieldCheck size={12}/> Grounded in retrieved product information</span><span>Enter to send · Shift + Enter for new line</span></div></div>
          </section>
        </div>

        <section className="workflow" id="workflow"><div className="workflow-title"><div className="panel-kicker">UNDER THE HOOD</div><h2>From product page to useful answers</h2><p>A simple Retrieval-Augmented Generation workflow.</p></div><div className="workflow-steps"><div className="workflow-step"><span className="workflow-num">01</span><div className="workflow-icon"><Globe2 size={19}/></div><b>Extract</b><p>Read accessible product page text.</p></div><div className="workflow-arrow"><ArrowRight size={17}/></div><div className="workflow-step"><span className="workflow-num">02</span><div className="workflow-icon"><FileText size={19}/></div><b>Chunk & embed</b><p>Split text and create vector embeddings.</p></div><div className="workflow-arrow"><ArrowRight size={17}/></div><div className="workflow-step"><span className="workflow-num">03</span><div className="workflow-icon"><BookOpenText size={19}/></div><b>Retrieve</b><p>Find chunks relevant to the question.</p></div><div className="workflow-arrow"><ArrowRight size={17}/></div><div className="workflow-step"><span className="workflow-num">04</span><div className="workflow-icon"><Sparkles size={19}/></div><b>Generate</b><p>LLM answers using retrieved evidence.</p></div></div></section>
        <footer className="footer"><button className="footer-brand" onClick={resetWorkspace}><span className="brand-mark small"><Sparkles size={15}/></span> PriceLens AI</button><span>Product knowledge, made simple.</span><span className="footer-privacy"><ShieldCheck size={13}/> No login required</span></footer>
      </div>
    </main>
  </div>
}

export default App
