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

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadFriendPrices() {
  const box = document.getElementById("friendPricesBox");
  const status = document.getElementById("friendPricesStatus");
  const rows = document.getElementById("friendPricesRows");
  box.style.display = "block";
  status.textContent = "Chargement...";
  rows.innerHTML = "";

  const res = await fetch("/prices/public/friend");
  const data = await res.json();

  if (!res.ok || !data.ok) {
    status.textContent = "Impossible de récupérer les prix (service indisponible).";
    return;
  }

  const items = data.items || [];
  status.textContent = items.length ? `${items.length} item(s)` : "Aucun item.";

  rows.innerHTML = items
    .map(
      (it) => `
      <div class="trow">
        <div class="label">${escapeHtml(it.article)}</div>
        <div class="price">${Number(it.prix).toFixed(2)} €</div>
        <div></div>
      </div>`
    )
    .join("");
}

document.addEventListener("click", (e) => {
  const btn = e.target.closest("#btnFriendPrices");
  if (!btn) return;

  btn.disabled = true;
  loadFriendPrices()
    .catch(() => alert("Erreur lors du chargement des prix publics."))
    .finally(() => (btn.disabled = false));
});