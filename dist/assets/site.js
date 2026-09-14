document.querySelectorAll('.copy').forEach(button=>button.addEventListener('click',async()=>{
  const box=button.closest('.example');
  const status=box.querySelector('.copy-status');
  try{await navigator.clipboard.writeText(box.querySelector('pre').textContent);status.textContent='확인 메모를 복사했습니다.';}
  catch{status.textContent='자동 복사를 사용할 수 없습니다. 메모 내용을 직접 선택해 복사해주세요.';}
}));
