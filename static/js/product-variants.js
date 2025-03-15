function updateVariants() {
    // Get the selected category radio button
    const selectedCategory = document.querySelector('input[name="product_category"]:checked');

    // Prepare variant fields container
    const variantContainer = document.getElementById('category-variants');
    variantContainer.innerHTML = ''; // Clear existing variant fields

    if (selectedCategory) {
        const category = selectedCategory.value;

        // Create variants based on the selected category
        if (category === 'wallet') {
            variantContainer.innerHTML += `
                <div class="row gx-3">
                    <div class="col-md-4 mb-3">
                        <label for="product_color1" class="form-label">Color1</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_color1" name="color1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_color2" class="form-label">Color2</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_color2" name="color2">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_color3" class="form-label">Color3</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_color3" name="color3">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_quantity1" class="form-label">Quantity for color1</label>
                        <input type="number" class="form-control" id="product_quantity1" name="quantity1" min="1" value="1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_quantity2" class="form-label">Quantity for color2</label>
                        <input type="number" class="form-control" id="product_quantity2" name="quantity2" min="1" value="1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_quantity3" class="form-label">Quantity for color3</label>
                        <input type="number" class="form-control" id="product_quantity3" name="quantity3" min="1" value="1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_charmImg1" class="form-label">Charm Image 1</label>
                        <input type="file" class="form-control" id="product_charmImg1" name="charmImg1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_charm1" class="form-label">Charm 1</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_charm1" name="charm1">
                    </div>
                </div>
                <div class="row gx-3">
                    <div class="col-md-4 mb-3">
                        <label for="product_charmImg2" class="form-label">Charm Image 2</label>
                        <input type="file" class="form-control" id="product_charmImg2" name="charmImg2">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_charm2" class="form-label">Charm 2</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_charm2" name="charm2">
                    </div>
                </div>
                <div class="row gx-3">
                    <div class="col-md-4 mb-3">
                        <label for="product_charmImg3" class="form-label">Charm Image 3</label>
                        <input type="file" class="form-control" id="product_charmImg3" name="charmImg3">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_charm3" class="form-label">Charm 3</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_charm3" name="charm3">
                    </div>
                </div>`;
        }

        if (category === 'water bottle') {
            variantContainer.innerHTML += `
                <div class="row gx-3">
                    <div class="col-md-4 mb-3">
                        <label for="product_liter1" class="form-label">litre 1</label>
                        <input type="text" placeholder="Type liter amount" class="form-control" id="product_liter1" name="liter1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_liter2" class="form-label">litre 2</label>
                        <input type="text" placeholder="Type liter amount" class="form-control" id="product_liter2" name="liter2">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_liter3" class="form-label">litre 3</label>
                        <input type="text" placeholder="Type liter amount" class="form-control" id="product_liter3" name="liter3">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_quantity1" class="form-label">Quantity for litre 1</label>
                        <input type="number" class="form-control" id="product_quantity1" name="quantity1" min="1" value="1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_quantity2" class="form-label">Quantity for litre 2</label>
                        <input type="number" class="form-control" id="product_quantity2" name="quantity2" min="1" value="1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_quantity3" class="form-label">Quantity for litre 3</label>
                        <input type="number" class="form-control" id="product_quantity3" name="quantity3" min="1" value="1">
                    </div>
                </div>`;
        }

        if (category === '3d crystal') {
            variantContainer.innerHTML += `
                <div class="row gx-3">
                    <div class="col-md-4 mb-3">
                        <label for="product_size1" class="form-label">Size1</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_size1" name="size1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_size2" class="form-label">Size2</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_size2" name="size2">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_size3" class="form-label">Size3</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_size3" name="size3">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_quantity1" class="form-label">Quantity for Size1</label>
                        <input type="number" class="form-control" id="product_quantity1" name="quantity1" min="1" value="1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_quantity2" class="form-label">Quantity for Size2</label>
                        <input type="number" class="form-control" id="product_quantity2" name="quantity2" min="1" value="1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_quantity3" class="form-label">Quantity for Size3</label>
                        <input type="number" class="form-control" id="product_quantity3" name="quantity3" min="1" value="1">
                    </div>
                </div>
                <div class="row gx-3">
                    <div class="col-md-4 mb-3">
                        <label for="product_viewFlex1" class="form-label">ViewFlex 1</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_viewFlex1" name="viewflex1">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_viewFlex2" class="form-label">ViewFlex 2</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_viewFlex2" name="viewflex2">
                    </div>
                    <div class="col-md-4 mb-3">
                        <label for="product_viewFlex3" class="form-label">ViewFlex 3</label>
                        <input type="text" placeholder="Type here" class="form-control" id="product_viewFlex3" name="viewflex3">
                    </div>
                </div>`;
        }

        // Add more categories as needed...
    }
}

// Add event listeners to the radio buttons
document.querySelectorAll('input[name="product_category"]').forEach(radio => {
    radio.addEventListener('change', updateVariants);
});
