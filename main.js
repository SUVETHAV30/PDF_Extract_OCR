document.addEventListener("DOMContentLoaded", async () => {
    // Fetch products.json
    const response = await fetch("./data.json");
    const data = await response.json();
    const product = data.products[0]; // assuming one product

    // Replace product info
    document.querySelector("title").textContent = `${product.product_name} - Maruyama`;
    document.querySelector(".breadcrumb-content").textContent = `Home / ${product.category} / ${product.product_name}`;
    document.querySelector(".product-info h1").textContent = product.product_name;
    document.querySelector(".category span").textContent = product.category;
    document.querySelector(".description").textContent = product.product_description;
    document.querySelector(".stars").textContent = `★ ${product.rating}`;
    document.querySelector(".rating-text").textContent = `(${product.reviewCount})`;

    // Main image
    document.querySelector(".main-image img").src = product.mainImage;
    document.querySelector(".main-image img").alt = product.product_name;

    // // Thumbnails
    const thumbnailsContainer = document.querySelector(".thumbnails");
    thumbnailsContainer.innerHTML = ""; // clear existing

    product.thumbnails.forEach((thumb, i) => {
        const div = document.createElement("div");
        div.classList.add("thumbnail");
        if (i === 0) div.classList.add("active");

        const img = document.createElement("img");
        img.src = thumb;
        img.alt = `Thumbnail ${i+1}`;
        img.style.width = "100%";
        img.style.height = "100%";
        img.style.objectFit = "cover";
        img.style.borderRadius = "3px";

        // On click, update main image
        div.addEventListener("click", () => {
            document.querySelectorAll(".thumbnail").forEach(el => el.classList.remove("active"));
            div.classList.add("active");
            document.querySelector(".main-image img").src = thumb;
        });

        div.appendChild(img);
        thumbnailsContainer.appendChild(div);
    });

    // Detailed Description
    document.querySelectorAll(".collapsible-content")[0].innerHTML = product.detailedDescription;

    // Features - Fixed to properly render images
    const combinedList = product.features.map((f, i) => {
        // Get the thumbnail image for this feature (cycle through thumbnails if needed)
        const imageUrl = product.thumbnails[i % product.thumbnails.length] || product.mainImage;

        // Extract key and value from the feature object
        const [title, description] = Object.entries(f)[0];

        return `
            <li>
                <img src="${imageUrl}" alt="${title}" style="width: 100%; height: 146px; object-fit: cover; border-radius: 5px;" 
                     onerror="this.style.display='none'; this.nextElementSibling.style.marginTop='0';" />
                <div style="padding: 10px 0;">
                    <strong style="color: #333; font-size: 14px;">${title}</strong><br>
                    <span style="color: #666; font-size: 12px; line-height: 1.4;">${description}</span>
                </div>
            </li>
        `;
    }).join("");

    // Render to DOM
    document.querySelectorAll(".collapsible-content")[1].innerHTML = `<ul class="feature-grid">${combinedList}</ul>`;

    // Specifications
    const specRows = product.specifications.map(spec => `
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: 600;">${spec.label}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">${spec.value}</td>
        </tr>
    `).join("");
    document.querySelectorAll(".collapsible-content")[2].innerHTML = `<table style="width: 100%; border-collapse: collapse;">${specRows}</table>`;
});