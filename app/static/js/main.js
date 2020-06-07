
/*price range*/
$('#sl2').slider();

var RGBChange = function() {
    $('#RGB').css('background', 'rgb(' + r.getValue() + ',' + g.getValue() + ',' + b.getValue() + ')')
};

/*scroll to top*/

$(document).ready(function() {
    $(function() {
        $.scrollUp({
            scrollName: 'scrollUp', // Element ID
            scrollDistance: 300, // Distance from top/bottom before showing element (px)
            scrollFrom: 'top', // 'top' or 'bottom'
            scrollSpeed: 300, // Speed back to top (ms)
            easingType: 'linear', // Scroll to top easing (see http://easings.net/)
            animation: 'fade', // Fade, slide, none
            animationSpeed: 200, // Animation in speed (ms)
            scrollTrigger: false, // Set a custom triggering element. Can be an HTML string or jQuery object
            //scrollTarget: false, // Set a custom target element for scrolling to the top
            scrollText: '<i class="fa fa-angle-up"></i>', // Text for element, can contain HTML
            scrollTitle: false, // Set a custom <a> title if required.
            scrollImg: false, // Set true to use image
            activeOverlay: false, // Set CSS color to display scrollUp active point, e.g '#00FFFF'
            zIndex: 2147483647 // Z-Index for the overlay
        });
    });
});

/* cart checkout calculations */

setTimeout(function() {
    $('#cart_messages').fadeOut(3000);
}, 5000);

var max_items_in_cart = 30

function inputValidate(item_id) {
    return isNaN(parseInt(document.getElementById('item' + item_id).value, 10))
}

function increaseValue(item_id) {
    var cart_value = parseInt(document.getElementById('item' + item_id).value, 10);
    cart_value = isNaN(cart_value) ? 0 : cart_value;
    if (cart_value > max_items_in_cart - 1) {
        alert("Maximum amount reached");
    }
    cart_value > max_items_in_cart - 1 ? cart_value = max_items_in_cart : cart_value++;
    if (document.getElementById('item' + item_id).value == cart_value) {
        return
    }
    if (cart_value == 2) {
        if (document.getElementById('apiece_value' + item_id).innerText == '') {
            document.getElementById('apiece_value' + item_id).innerText = document.getElementById('item_total_value' + item_id).innerText + ' apiece'
        }
    }
    document.getElementById('item' + item_id).value = cart_value;
    document.getElementById("right-side-item-price" + item_id).innerText = "x " + cart_value;
    console.log(cart_value);
    calculate_cart(cart_value, item_id);
}

$('#increase_cart').click(function() {
    var item_id = $(this).closest('div').attr('id');
    increaseValue(item_id);
    return false;
});

$('#decrease_cart').click(function() {
    var item_id = $(this).closest('div').attr('id');
    decreaseValue(item_id);
    return false;
});


function decreaseValue(item_id) {
    var cart_value = parseInt(document.getElementById('item' + item_id).value, 10);
    cart_value = isNaN(cart_value) ? 1 : cart_value;
    cart_value <= 2 ? cart_value = 1 : cart_value--;
    if (document.getElementById('item' + item_id).value == cart_value) {
        return
    }
    if (cart_value == 1) {
        if (document.getElementById('apiece_value' + item_id).innerText != '') {
            document.getElementById('apiece_value' + item_id).innerText = ''
        }
    }
    document.getElementById('item' + item_id).value = cart_value;

    var right_side_value = cart_value > 1 ? right_side_value = "x " + cart_value : right_side_value = "";
    document.getElementById("right-side-item-price" + item_id).innerText = right_side_value;

    calculate_cart(cart_value, item_id);
}

function updateValue(item_id) {
    var cart_value = parseInt(document.getElementById('item' + item_id).value, 10);
    cart_value = isNaN(cart_value) ? 1 : cart_value;
    cart_value < 1 ? cart_value = 1 : '';
    cart_value > max_items_in_cart ? cart_value = max_items_in_cart : '';

    if (cart_value == 1) {
        document.getElementById('apiece_value' + item_id).innerText = ''
    } else {
        if (document.getElementById('apiece_value' + item_id).innerText == '') {
            document.getElementById('apiece_value' + item_id).innerText = document.getElementById('item_total_value' + item_id).innerText + ' apiece'
        }
    }
    document.getElementById('item' + item_id).value = cart_value;

    var right_side_value = cart_value > 1 ? right_side_value = "x " + cart_value : right_side_value = "";
    document.getElementById("right-side-item-price" + item_id).innerText = right_side_value;

    calculate_cart(cart_value, item_id);
}

function removePromo(cart_id) {
    add_loader();
    $.ajax({
        url: '/purchase/checkout/delete_promo_code/',
        type: 'POST',
        headers: {
                'X-CSRFTOKEN': getCookie('csrftoken')
        },
        data: {
            'cart_id': cart_id
        },
        dataType: 'json',
        success: function() { location.reload(); },
        error: function() {
            console.log("Error!");
            $("div.loading_contener").remove();
            alert("Something went wrong! Try again later");
        }
    });
}

function errorAjax()
{
    alert("Something went wrong! Try again later");
    $("div.loading_contener").remove();
}

function addFavorite(prod_id) {
    add_loader();
    $.ajax({
        url: '/account/add_favorite_product/',
        type: 'POST',
        headers: {
                'X-CSRFTOKEN': getCookie('csrftoken')
        },
        data: {
            'prod_id': prod_id
        },
        dataType: 'json',
        success: function(data) {
            if(data.success){
                $("#add_fav"+prod_id).remove();
                var elem = document.getElementById("remove_fav"+prod_id);
                if(!elem){
                    var delete_item_button = '<button id="remove_fav'+ prod_id +'" onclick="removeFavorite('+ prod_id +'); return false;" class="btn btn-outline-danger btn-xs mx-2"><i class="fas fa-heart"></i> Delete from favorites</button>'
                    var x = document.getElementsByClassName("cart-fav-box");
                    x[0].insertAdjacentHTML("beforeEnd", delete_item_button);
                }
                alert("Product added to favorites");
                $("div.loading_contener").remove();
            }
        },
        error: errorAjax
    });
}

function removeFavorite(prod_id) {
    var q = confirm("Do you want to delete product from favorites?");
    add_loader();
    if (q == true) {
    $.ajax({
        url: '/account/delete_favorite_product/',
        type: 'POST',
        headers: {
                'X-CSRFTOKEN': getCookie('csrftoken')
        },
        data: {
            'prod_id': prod_id
        },
        dataType: 'json',
        success: function() {
            $("#favorite"+prod_id).remove();
            $("#remove_fav"+prod_id).remove();
            var elem = document.getElementById("add_fav");
            if(!elem){
                var add_item_button = '<button id="add_fav'+ prod_id +'" onclick="addFavorite('+ prod_id +'); return false;" class="btn btn-info mx-2"><i class="fas fa fa-heart"></i> Add to favorites</button>'
                var x = document.getElementsByClassName("cart-fav-box");
                if(x[0]){
                    x[0].insertAdjacentHTML("beforeEnd", add_item_button);
                }
            }
            alert("Product deleted from favorites");
        },
        error: errorAjax
    });}
    $("div.loading_contener").remove();
}

function rateProduct(prod_id) {
    var e = document.getElementById("select_rate");
    var rating = e.options[e.selectedIndex].value;
    if(rating>0){
        add_loader();
        $.ajax({
            url: '/products/rate/',
            type: 'POST',
            headers: {
                    'X-CSRFTOKEN': getCookie('csrftoken')
            },
            data: {
                'prod_id': prod_id,
                'score': rating
            },
            dataType: 'json',
            success: function(data) {
                $("#rating"+prod_id).remove();
                var elem = document.getElementById("rated_products");
                if(elem){
                    body = elem.getElementsByTagName('tbody')[0];
                    if(body){
                        // Insert a row in the table at the last row
                        //var newRow   = body.insertRow();

                        // Insert a cell in the row at index 0
                        //var newCell  = newRow.insertCell(0);

                            //cart_list.innerText = "";
                            var row_content = `<tr id="favorite`+ data.rating.product.id +`">
                                <th style="width:15%" scope="row"><a href="`+ data.rating.product.get_absolute_url +`">
                                <img src="`+ data.rating.product.thumbnail.url +`" alt="`+ data.rating.product.name +`"></a>
                                    </th>
                                <td style="width:60%"><a href="`+ data.rating.product.get_absolute_url +`">
                                        <p>`+ data.rating.product.name +`</p>
                                    </a></td>
                                <td style="width:25%">Score: `+ data.rating.score  +`/5</td>
                            </tr>`;

                            body.insertAdjacentHTML("beforeend", row_content);
                    }



                        // Append a text node to the cell
                        //var newText  = document.createTextNode('New row');
                        //newCell.appendChild(newText);
                }
                alert("Product rated");
            },
            error: errorAjax
        });
        $("div.loading_contener").remove();
    } else { alert('You need to choose number to rate')}
}


function calculate_cart(cart_value, item_id) {
    add_loader();
    $.ajax({
        url: '/purchase/cart/calculate/',
        type: 'POST',
        data: {
            'cart_value': cart_value,
            'item_id': item_id
        },
        dataType: 'json',
        success: function(data) {
            if (data.success) {
                if (data.item_total_value) {
                    document.getElementById("item_total_value" + item_id).innerText = data.item_total_value
                }
                if (data.old_price_checkout) {
                    document.getElementById("old-price-checkout" + item_id).innerText = data.old_price_checkout
                }
                if (data.cart_total_value) {
                    document.getElementById("cart_total_value").innerText = data.cart_total_value
                    document.getElementById("right-side-cart-total-value").innerText = data.cart_total_value
                }
                if (data.cart_qty) {
                    document.getElementById("cart-qty").innerText = data.cart_qty;
                    document.getElementById("right-side-cart-qty").innerText = data.cart_qty;
                }
            } else if (data.remove_cart) {
                console.log("No success");
                //window.location.replace("/cart/");
            }
            $("div.loading_contener").remove();
            },
            error: errorAjax
    });
}

function add_to_cart(item_id) {
    add_loader();
    var CSRF_TOKEN = getCookie('csrftoken');
    var elem3 = document.getElementById("delete_item_button" + item_id);
    if(!elem3){
        var add_item_button = document.getElementById("add_item_button" + item_id);
        if(add_item_button){
            var delete_item_button = '<button id="delete_item_button'+ item_id +'" onclick="delete_from_cart('+ item_id +'); return false;" class="btn btn-danger ml-2">Delete from cart</button>'
            add_item_button.insertAdjacentHTML("afterend", delete_item_button);
        }

    }
    $.ajax({
        url: '/purchase/cart/add_item/',
        type: 'POST',
        headers: {
            'X-CSRFTOKEN': CSRF_TOKEN
        },
        data: {
            'item_id': item_id
        },
        dataType: 'json',
        success: function(data) {
            if (data.success) {
                console.log("Success");
                console.log(data.success);
                console.log(data.item_id);
                document.getElementById("cart-qty").innerText = data.cart_qty;
                if (data.new_cart) {
                    var start_cart = `
                    <h5 class="py-3">Summary</h5>
                    <ul class="summary-table pb-10">
                        <li><span>Total: </span> <span id="right-side-cart-total-value">{{ cart.get_cart_total }}</span></li>
                    </ul>
                    <a href="` + data.cart_url + `" ><button class="btn-lg my-3 px-5 btn btn-dark"><i class="fas fa-shopping-cart"></i>
 Cart</button></a>
                    `;
                    var cart_list = document.getElementById("cart-list");
                    if (cart_list) {
                        cart_list.innerText = "";
                        cart_list.insertAdjacentHTML("beforeend", start_cart);
                    }
                }
                document.getElementById("right-side-cart-qty").innerText = data.cart_qty;

                var right_side_cart_total_value = document.getElementById("right-side-cart-total-value")
                if (right_side_cart_total_value) {
                    right_side_cart_total_value.innerText = data.cart_total_value;
                }

                var cart_total_value = document.getElementById("cart_total_value");
                if (cart_total_value) {
                    cart_total_value.innerText = data.cart_total_value;
                }
                if (data.amount) {
                    document.getElementById("right-side-item-price" + data.item_id).innerText = "x " + data.amount;
                }
                if (data.new_item) {
                    var new_item = `
                    <div id="right-side-item` + data.item_id + `" class="single-cart-item">
                        <a href="` + data.product_url + `">
                            <img src="` + data.product_thumbnail_url + `" class="cart-thumb" alt=""></a>
                            <div class="cart-item-desc pb-2">
                              <span class="product-remove"><i class="fa fa-close" aria-hidden="true"></i></span>
                                <span>` + data.product_subdepartment_name + `</span>
                                <br><h6>` + data.product_name + `</h6>
                                <span class="price">` + data.product_price + `
                                    <item-price id="right-side-item-price` + data.item_id + `"></item-price>
                                </span>
                                <br><button id="delete_item_button" onclick="delete_from_cart(` + data.item_id + `); return false;" class="btn btn-danger btn-sm"><i class="fas fa-trash-alt"></i> Delete from cart</button>
                            </div>
                    </div>
                    `;
                    var cart_list = document.getElementById("cart-list");
                    if (cart_list) {
                        cart_list.insertAdjacentHTML("beforeend", new_item);
                    }
                }
                alert("Added product to cart");
            } else {
                console.log("Failed");
            }
            $("div.loading_contener").remove();
        },
        error: errorAjax
    });
}

function delete_from_cart(item_id) {
    var CSRF_TOKEN = getCookie('csrftoken');
    add_loader();
    $.ajax({
        url: '/purchase/cart/delete_item/',
        type: 'POST',
        headers: {
            'X-CSRFTOKEN': CSRF_TOKEN
        },
        data: {
            'item_id': item_id
        },
        dataType: 'json',
        success: function(data) {
            var delete_item_button = document.getElementById("delete_item_button" + item_id);
            if (delete_item_button) {
                delete_item_button.remove();
            }
            if (data.success) {
                var elem1 = document.getElementById("row" + item_id);
                if (elem1) {
                    elem1.parentNode.removeChild(elem1);
                }
                var elem2 = document.getElementById("right-side-item" + item_id);
                if (elem2) {
                    elem2.parentNode.removeChild(elem2);
                }
                if (data.cart_total_value) {
                    var cart_total_value = document.getElementById("cart_total_value")
                    if(cart_total_value){
                        cart_total_value.innerText = data.cart_total_value;
                    }
                    document.getElementById("right-side-cart-total-value").innerText = data.cart_total_value;
                }
                if (data.cart_qty) {
                    document.getElementById("cart-qty").innerText = data.cart_qty;
                    document.getElementById("right-side-cart-qty").innerText = data.cart_qty;
                }
                alert("Product deleted from cart");
            } else if (data.remove_cart) {
                var card_body = document.getElementById("card-body");
                if (card_body) {
                    card_body.parentNode.removeChild(card_body);
                }
                var card_footer = document.getElementById("card-footer");
                if (card_footer) {
                    card_footer.parentNode.removeChild(card_footer);
                }
                var shopping_cart = document.getElementById("shopping-cart");
                if (shopping_cart) {
                    var empty_cart = `
                    <div id="card-body" class="card-body">
                        <br><h5><span class="py-5 px-5">Your cart is empty</span></h5><br>
                    </div>
                    `;
                    shopping_cart.insertAdjacentHTML("beforeend", empty_cart);
                }
                document.getElementById("cart-qty").innerText = "";
                document.getElementById("right-side-cart-qty").innerText = "";
                var cart_list = document.getElementById("cart-list")
                if (cart_list) {
                    cart_list.innerText = "";
                    var right_side_empty_cart = `
                    <br><h5>Your cart is empty</h5>
                    `;
                    cart_list.insertAdjacentHTML("beforeend", right_side_empty_cart);
                }
                console.log("Removed cart");
                alert("Product deleted from cart");
            }
            if (data.ups) {
                console.log("Ups!");
            }
            $("div.loading_contener").remove();
        },
        error: errorAjax
    });
}

function delete_cart() {
    var q = confirm("Do you want to delete shipping cart?");
    add_loader();
    if (q == true) {
        $.ajax({
            url: '/purchase/delete/',
            type: 'POST',
            dataType: 'json',
            success: function(data) {
                if (data.success) {
                    console.log("Success");
                    var card_body = document.getElementById("card-body");
                    if (card_body) {
                        card_body.parentNode.removeChild(card_body);
                    }
                    var card_footer = document.getElementById("card-footer");
                    if (card_footer) {
                        card_footer.parentNode.removeChild(card_footer);
                    }
                    var shopping_cart = document.getElementById("shopping-cart");
                    if (shopping_cart) {
                        var empty_cart = `
                        <div id="card-body" class="card-body">
                            <br><h5><span class="py-5 px-5">Your cart is empty</span></h5><br>
                        </div>
                        `;
                        shopping_cart.insertAdjacentHTML("beforeend", empty_cart);
                    }
                    document.getElementById("cart-qty").innerText = "";
                    document.getElementById("right-side-cart-qty").innerText = "";
                    var cart_list = document.getElementById("cart-list")
                    if (cart_list) {
                        cart_list.innerText = "";
                        var right_side_empty_cart = `
                        <br><h5>Your cart is empty</h5>
                        `;
                        cart_list.insertAdjacentHTML("beforeend", right_side_empty_cart);
                    }
                    console.log("Removed cart");
                    alert("Shipping cart has been deleted.")
                    $("div.loading_contener").remove();
                }
            },
            error: errorAjax
        });
    } else {$("div.loading_contener").remove();}
}

function getOrdering(selectObject) {
    // get current url
    var url = new URL(window.location.href)

    // search parameters from current url
    var search_params = url.searchParams;

    // set of
    var ordering = {
        "HiRated": "rating",
        "Newest": "-creationdate",
        "HiPrice": "-price",
        "LowPrice": "price"
    };

    // new value of "ordering"
    search_params.set('ordering', ordering[selectObject.value]);

    // change the search property of the main url
    url.search = search_params.toString();

    // the new url string
    var new_url = url.toString();

    // go to new page
    window.location.href = new_url;
}

function setFilterCheckboxes() {

    var brands_div = document.getElementById("brands");
    var discount = document.getElementById("showDiscounts");

        // get current url
        var url = new URL(window.location.href);

        // search parameters from current url
        var search_params = url.searchParams;

    if(brands_div){

        if (search_params.get('brand')) {
            search_params.forEach(function(value, key) {
                var input = document.getElementById(value)
                console.log(value)
                console.log(input)
                if (input) {
                    input.checked = true;
                }
            });
        } else {
            document.getElementById("allBrands").checked = true;
            document.getElementById("allBrands").disabled = true;
        }
    }

    if(discount){
        if(search_params.get('discountonly')){
            discount.checked = true;
        }
    }
}

setFilterCheckboxes()

function getBrand(brandSlug) {
    // get current url
    var url = new URL(window.location.href)
    brandSlug.checked = true
    // search parameters from current url
    var search_params = url.searchParams;
    if (brandSlug.id == "allBrands") {
        search_params.delete('brand');
        url.search = search_params.toString();
        var new_url = url.toString();
        window.location.href = new_url;
    } else {
        var delete_brand_from_get = false
        search_params.forEach(function(value, key) {
            console.log("key: " + key + ", value: " + value)
            if (value == brandSlug.id) {
                delete_brand_from_get = true
            }
        });

        if (delete_brand_from_get) {
            var new_url = new URL(window.location.href)
            // set search property to blank
            new_url.search = '';
            var new_params = new_url.searchParams
            search_params.forEach(function(value, key) {
                if (value != brandSlug.id) {
                    // new value of brand filter
                    if (search_params.get('brand')) {
                        new_params.append(key, value);
                    } else {
                        new_params.set(key, value);
                    }
                    console.log("Yes: key - " + key + ", value - " + value + ", brandSlug.id - " + brandSlug.id);
                }
            });
            // change the search property of the main url
            new_url.search = new_params.toString();
            url = new_url.toString()
            window.location.href = url;
        } else {
            // new value of brand filter
            if (search_params.get('brand')) {
                search_params.append('brand', brandSlug.id);
            } else {
                search_params.set('brand', brandSlug.id);
            }

            url.search = search_params.toString();
            var new_url = url.toString();
            window.location.href = new_url;
        }
    }
}

function getDiscountsOnly() {
    // get current url
    var url = new URL(window.location.href)

    // search parameters from current url
    var search_params = url.searchParams;

    var already_showing = search_params.get('discountonly');

    if (already_showing) {
        var new_url = new URL(window.location.href)
        // set search property to blank
        search_params.delete('discountonly');
    } else {
        search_params.set('discountonly', 'true');
    }
    url_search = search_params.toString();
    var new_url = url.toString();
    window.location.href = new_url;
}