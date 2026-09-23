const $ = (id)=>document.getElementById(id);
const desc=$('description'), imgInput=$('image'), drop=$('dropZone'), thumb=$('previewThumb'), imgPrev=$('imagePreview'), removeImage=$('removeImage');
const generate=$('generateBtn'), status=$('status'), mapPreview=$('mapPreview'), empty=$('emptyState'), dlBar=$('downloadBar'), dl=$('downloadLitematic'), png=$('openPng'), meta=$('resultMeta'), planDetails=$('planDetails'), planJson=$('planJson');

imgInput.onchange=()=>{const f=imgInput.files?.[0];if(!f)return;const r=new FileReader();r.onload=()=>{thumb.src=r.result;imgPrev.hidden=false;drop.style.display='none'};r.readAsDataURL(f)};
removeImage.onclick=()=>{imgInput.value='';imgPrev.hidden=true;drop.style.display='flex'};
drop.ondragover=e=>{e.preventDefault();drop.style.borderColor='#69d13a'};
drop.ondragleave=()=>drop.style.borderColor='';
drop.ondrop=e=>{e.preventDefault();drop.style.borderColor='';if(!e.dataTransfer.files?.[0])return;imgInput.files=e.dataTransfer.files;imgInput.dispatchEvent(new Event('change'))};

generate.onclick=async()=>{
 const text=desc.value.trim();
 if(!text){setStatus('נא לכתוב תיאור של הבנייה.','err');desc.focus();return}
 const fd=new FormData();fd.append('description',text);if(imgInput.files?.[0])fd.append('image',imgInput.files[0]);
 generate.disabled=true;generate.innerHTML='יוצר את המבנה… <span>◌</span>';setStatus('בונה את המפה מקומית — ללא OpenAI API וללא תשלום על AI.');
 try{const r=await fetch('/api/build',{method:'POST',body:fd});const data=await r.json();if(!r.ok)throw new Error(data.detail||'שגיאה לא ידועה');showResult(data);setStatus(`נוצר: ${data.name} • ${data.stats.blocks.toLocaleString()} בלוקים • ${data.stats.palette_size} מצבי בלוק`,'ok')}
 catch(e){setStatus(e.message,'err')}finally{generate.disabled=false;generate.innerHTML='צור מבנה <span>→</span>'}
};
function setStatus(t,k=''){status.hidden=false;status.className='status '+k;status.textContent=t}
function showResult(data){meta.textContent=`${data.name} • ${data.size.x}×${data.size.y}×${data.size.z}`;mapPreview.src=data.preview+'?t='+Date.now();mapPreview.hidden=false;empty.hidden=true;dlBar.hidden=false;dl.href=data.litematic;dl.download=(data.name||'build')+'.litematic';png.href=data.preview;planDetails.hidden=false;planJson.textContent=JSON.stringify(data.plan,null,2);document.querySelector('.result-panel').scrollIntoView({behavior:'smooth',block:'start'})}
const grid=$('miniGrid');if(grid){for(let i=0;i<108;i++){const s=document.createElement('span');grid.appendChild(s)}}
