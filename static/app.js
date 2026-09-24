const $ = (id) => document.getElementById(id);

const desc = $("description");
const imgInput = $("image");
const drop = $("drop");
const thumb = $("thumb");
const thumbWrap = $("thumbWrap");
const removeBtn = $("remove");

const generate = $("go");
const status = $("status");
const mapPreview = $("map");
const empty = $("empty");
const actions = $("actions");
const dl = $("litematic");
const png = $("png");
const meta = $("meta");
const voxels = $("voxels");

function setStatus(text, kind = "") {
  if (!status) return;
  status.hidden = false;
  status.className = "status " + kind;
  status.textContent = text;
}

if (imgInput) {
  imgInput.addEventListener("change", () => {
    const file = imgInput.files?.[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = () => {
      if (thumb) {
        thumb.src = reader.result;
      }

      if (thumbWrap) {
        thumbWrap.hidden = false;
      }

      if (drop) {
        drop.style.display = "none";
      }
    };

    reader.readAsDataURL(file);
  });
}

if (removeBtn) {
  removeBtn.addEventListener("click", (event) => {
    event.preventDefault();

    if (imgInput) {
      imgInput.value = "";
    }

    if (thumb) {
      thumb.src = "";
    }

    if (thumbWrap) {
      thumbWrap.hidden = true;
    }

    if (drop) {
      drop.style.display = "";
    }
  });
}

if (drop && imgInput) {
  drop.addEventListener("dragover", (event) => {
    event.preventDefault();
    drop.style.borderColor = "#69d13a";
  });

  drop.addEventListener("dragleave", () => {
    drop.style.borderColor = "";
  });

  drop.addEventListener("drop", (event) => {
    event.preventDefault();
    drop.style.borderColor = "";

    const file = event.dataTransfer?.files?.[0];
    if (!file) return;

    try {
      const dt = new DataTransfer();
      dt.items.add(file);
      imgInput.files = dt.files;
      imgInput.dispatchEvent(new Event("change"));
    } catch (error) {
      console.error(error);
    }
  });
}

if (generate) {
  generate.addEventListener("click", async (event) => {
    event.preventDefault();

    const text = desc?.value.trim() || "";

    if (!text) {
      setStatus("נא לכתוב תיאור של הבנייה.", "err");
      desc?.focus();
      return;
    }

    const formData = new FormData();
    formData.append("description", text);

    const imageFile = imgInput?.files?.[0];
    if (imageFile) {
      formData.append("image", imageFile);
    }

    generate.disabled = true;
    generate.innerHTML = 'יוצר את המבנה… <span>◌</span>';

    setStatus("בונה את המפה מקומית — ללא OpenAI וללא תשלום על AI.");

    try {
      const response = await fetch("/api/build", {
        method: "POST",
        body: formData
      });

      const contentType =
        response.headers.get("content-type") || "";

      let data;

      if (contentType.includes("application/json")) {
        data = await response.json();
      } else {
        const raw = await response.text();
        throw new Error(
          raw || `שגיאת שרת (${response.status})`
        );
      }

      if (!response.ok) {
        throw new Error(
          data?.detail || "שגיאה ביצירת המבנה."
        );
      }

      showResult(data);

      const blocks = Number(
        data?.stats?.blocks || 0
      ).toLocaleString();

      setStatus(
        `נוצר: ${data.name} • ${blocks} בלוקים`,
        "ok"
      );
    } catch (error) {
      console.error(error);

      setStatus(
        error?.message || "שגיאה לא ידועה.",
        "err"
      );
    } finally {
      generate.disabled = false;
      generate.innerHTML =
        'צור את המבנה <span>→</span>';
    }
  });
}

function showResult(data) {
  if (meta) {
    meta.textContent =
      `${data.name} • ${data.size.x}×${data.size.y}×${data.size.z}`;
  }

  if (mapPreview) {
    mapPreview.src =
      data.preview + "?t=" + Date.now();

    mapPreview.hidden = false;
  }

  if (empty) {
    empty.hidden = true;
  }

  if (actions) {
    actions.hidden = false;
  }

  if (dl) {
    dl.href = data.litematic;
    dl.download =
      (data.name || "build") + ".litematic";
  }

  if (png) {
    png.href = data.preview;
  }

  document
    .querySelector(".result")
    ?.scrollIntoView({
      behavior: "smooth",
      block: "start"
    });
}

if (voxels) {
  for (let i = 0; i < 108; i++) {
    const cell = document.createElement("span");
    voxels.appendChild(cell);
  }
}
