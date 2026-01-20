async function deletePrice(id) {
  const res = await fetch(`/prices/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("delete failed");
  return await res.json();
}

document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".js-delete");
  if (!btn) return;

  const row = btn.closest("[data-price-id]");
  const id = row?.dataset?.priceId;
  if (!id) return;

  const ok = confirm("Supprimer ce prix ?");
  if (!ok) return;

  btn.disabled = true;
  try {
    await deletePrice(id);
    row.remove();
  } catch (err) {
    alert("Erreur suppression.");
    btn.disabled = false;
  }
});
