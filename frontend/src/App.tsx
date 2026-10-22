import {useEffect,useState,type FormEvent} from 'react';
import {UserCircle,CaretDown,SignOut,Eye,EyeSlash,List} from '@phosphor-icons/react';
import {api,post,setCSRF} from './api';
import {ErrorMessage} from './components/UI';
import {Uploads,Setup,Progress} from './pages/Uploads';
import {Review} from './pages/Review';
import {Incidents} from './pages/Incidents';

function Login({onLogin}:{onLogin:()=>void}){
 const [password,setPassword]=useState(''),[visible,setVisible]=useState(false),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError('');try{const session=await post<{csrf:string}>('/session',{password});setCSRF(session.csrf);onLogin();}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
 return <div className="login-page"><div className="wordmark">Industrial AI</div><form className="login-form" onSubmit={submit}><h1>Sign in</h1><p className="subtitle">Use your operator password to open this workspace.</p><label className="field" htmlFor="password">Password</label><div className="password-field"><input id="password" type={visible?'text':'password'} autoComplete="current-password" autoFocus value={password} onChange={e=>setPassword(e.target.value)} required maxLength={256}/><button type="button" aria-label={visible?'Hide password':'Show password'} onClick={()=>setVisible(!visible)}>{visible?<EyeSlash size={23}/>:<Eye size={23}/>}</button></div><ErrorMessage error={error}/><button className="primary" disabled={!password||busy}>{busy?'Signing in…':'Sign in'}</button><p className="help">Need access? Contact your workspace owner.</p></form><footer className="login-footer">Local workspace · Footage stays on this Mac.</footer></div>;
}

export function App(){
 const [auth,setAuth]=useState<boolean|null>(null),[route,setRoute]=useState(location.hash.slice(1)||'/uploads'),[menu,setMenu]=useState(false);
 useEffect(()=>{api<{csrf:string}>('/session').then(s=>{setCSRF(s.csrf);setAuth(true);}).catch(()=>setAuth(false));const hash=()=>{setRoute(location.hash.slice(1)||'/uploads');setMenu(false);window.scrollTo(0,0);};const out=()=>setAuth(false);window.addEventListener('hashchange',hash);window.addEventListener('signedout',out);return()=>{window.removeEventListener('hashchange',hash);window.removeEventListener('signedout',out);};},[]);
 if(auth===null)return <div className="initial-loading">Opening local workspace…</div>;
 if(!auth)return <Login onLogin={()=>setAuth(true)}/>;
 async function signOut(){await api('/session',{method:'DELETE'});setAuth(false);}
 const [section,id]=route.split('/').filter(Boolean),active=section==='history'?'history':section==='review'?'review':'uploads';
 return <><a className="skip-link" href="#main-content">Skip to content</a><header className="topbar"><a className="wordmark" href="#/uploads">Industrial AI</a><nav aria-label="Main navigation" className={menu?'open':''}>{[['uploads','Video library'],['review','Review'],['history','Incident history']].map(([value,label])=><a key={value} aria-current={active===value?'page':undefined} href={value==='review'?(section==='review'?location.hash:'#/uploads'):'#/'+value}>{label}</a>)}<button className="mobile-nav-action" onClick={signOut}><SignOut size={19}/>Sign out</button></nav><div className="operator"><UserCircle size={28}/><details><summary>Operator <CaretDown size={15}/></summary><button onClick={signOut}><SignOut size={19}/>Sign out</button></details></div><button className="icon-button mobile-menu" aria-label="Menu" aria-expanded={menu} onClick={()=>setMenu(!menu)}><List size={26}/></button></header><div id="main-content">{section==='setup'&&id?<Setup key={id} id={id}/>:section==='progress'&&id?<Progress key={id} id={id}/>:section==='review'&&id?<Review key={id} id={id}/>:section==='history'?<Incidents/>:<Uploads/>}</div></>;
}
