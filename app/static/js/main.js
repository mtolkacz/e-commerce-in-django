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

function removeItem(item_id) {
    var elem1 = document.getElementById("row" + item_id);
    if (elem1) {
        elem1.parentNode.removeChild(elem1);
    }
    var elem2 = document.getElementById("right-side-item" + item_id);
    if (elem2) {
        elem2.parentNode.removeChild(elem2);
    }
    var elem3 = document.getElementById("delete_item_button");
    if (elem3) {
        elem3.remove()
    }
    delete_from_cart(item_id);
}

function calculate_cart(cart_value, item_id) {
    $.ajax({
        url: '/cart/calculate/',
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
        }
    });
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function add_to_cart(item_id) {
    var CSRF_TOKEN = getCookie('csrftoken');
    var elem3 = document.getElementById("delete_item_button");
    if(!elem3){
        var add_item_button = document.getElementById("add_item_button");
        if(add_item_button){
            var delete_item_button = '<button id="delete_item_button" onclick="removeItem('+ item_id +'); return false;" class="btn btn-danger ml-2">Delete from cart</button>'
            add_item_button.insertAdjacentHTML("afterend", delete_item_button);
        }

    }
    $.ajax({
        url: '/cart/add_item/',
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
                        <li><span>TOTAL:</span> <span id="right-side-cart-total-value"></span></li>
                    </ul>
                    <br>
                    <div class="checkout-btn my-20">
                        <a href="` + data.checkout_url + `" class="btn essence-btn">check out</a>
                    </div>
                    <br>
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
                            <div class="cart-item-desc">
                              <span class="product-remove"><i class="fa fa-close" aria-hidden="true"></i></span>
                                <span>` + data.product_subdepartment_name + `</span>
                                <br><h6>` + data.product_name + `</h6>
                                <span class="price">` + data.product_price + `
                                    <item-price id="right-side-item-price` + data.item_id + `"></item-price>
                                </span>
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
        },
        error: function() {
            console.log("Error!");
            alert("Something went wrong!");
        }
    });
}

function delete_from_cart(item_id) {
    var CSRF_TOKEN = getCookie('csrftoken');
    $.ajax({
        url: '/cart/delete_item/',
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
            }
            if (data.ups) {
                console.log("Ups!");
            }
        }
    });
}

function delete_cart() {
    var q = confirm("Do you want to delete shipping cart?");
    if (q == true) {
        $.ajax({
            url: '/cart/delete_cart/',
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
                }
            }
        });
    }
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


function setBrandCheckboxes() {

    var brands_div = document.getElementById("brands");

    if(brands_div){
        // get current url
        var url = new URL(window.location.href);

        // search parameters from current url
        var search_params = url.searchParams;

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
}
setBrandCheckboxes()

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