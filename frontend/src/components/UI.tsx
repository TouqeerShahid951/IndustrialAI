import {useEffect,useRef,type ReactNode} from 'react';
import {Fire,CloudFog,Cigarette,HardHat,Polygon,WarningCircle,X,CheckCircle,XCircle,Question} from '@phosphor-icons/react';
import type {Kind} from '../api';
export const icons={fire:Fire,smoke:CloudFog,smoking:Cigarette,no_helmet:HardHat,intrusion:Polygon};
export function KindIcon({kind,size=24}:{kind:Kind;size?:number}){const Icon=icons[kind];return <Icon size={size} aria-hidden="true"/>;}
export function ErrorMessage({error}:{error:string}){return error?<div className="error" role="alert"><WarningCircle size={20}/><span>{error}</span></div>:null;}
export function Status({value}:{value:string}){const attention=['unreviewed','uncertain','partial','Needs review'].includes(value);const Icon=value==='confirmed'?CheckCircle:value==='false_alarm'?XCircle:value==='uncertain'?Question:null;return <span className={'status '+(attention?'attention':'')} >{Icon?<Icon size={18}/>:<span className="status-dot"/>}{({unreviewed:'Needs review',confirmed:'Confirmed incident',false_alarm:'False alarm',uncertain:'Uncertain'} as Record<string,string>)[value]||value.replaceAll('_',' ')}</span>;}
export function Modal({title,children,onClose,wide=false}:{title:string;children:ReactNode;onClose:()=>void;wide?:boolean}){
 const ref=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const element=ref.current;const previous=document.activeElement as HTMLElement;element?.showModal();return()=>{element?.close();previous?.focus();};},[]);
 return <dialog ref={ref} className={wide?'modal wide':'modal'} aria-labelledby="dialog-title" onCancel={e=>{e.preventDefault();onClose();}}><header className="dialog-header"><h2 id="dialog-title">{title}</h2><button className="icon-button" onClick={onClose} aria-label={'Close '+title}><X size={20}/></button></header>{children}</dialog>;
}
