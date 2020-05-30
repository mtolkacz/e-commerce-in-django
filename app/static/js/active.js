function validate_price(option){
    var validation = true
    var price_slider = document.getElementById("price-slider");
    var element_min = document.getElementById("min_price");
    var element_max = document.getElementById("max_price");
    var starts_with_currency = document.getElementById(option + "_price").value.startsWith("$");
    var parsed_value;

    if (starts_with_currency == false){
        parsed_value = parseInt(document.getElementById(option + "_price").value);
    } else {
        parsed_value = parseInt(document.getElementById(option + "_price").value.substring(1));
    }
    var data_min = price_slider.getAttribute("data-min");
    var data_max = price_slider.getAttribute("data-max");

    if (Number.isInteger(parsed_value) == false){
        if(option=='min'){
            element_min.value = price_slider.getAttribute("data-unit") + data_min;
        } else if(option=='max'){
            element_max.value = price_slider.getAttribute("data-unit") + data_max;
        }
        validation = false
    } else if (((parsed_value < data_min) || (parsed_value > element_max.value.substring(1))) && option=='min'){
        element_min.value = price_slider.getAttribute("data-unit") + data_min
        validation = false
    } else if ((parsed_value > data_max || parsed_value < element_min.value.substring(1)) && option=='max'){
        element_max.value = price_slider.getAttribute("data-unit") + data_max
        validation = false
    } else if (starts_with_currency == false){
        if(option=='min'){
            element_min.value = price_slider.getAttribute("data-unit") + element_min.value
        } else if(option=='max'){
            element_max.value = price_slider.getAttribute("data-unit") + element_max.value
        }
    }

    return validation
}

function set_price_parameters(){
    var url = new URL(window.location.href);
    var search_params = url.searchParams;

    search_params.set('price_min', document.getElementById("min_price").value.substring(1));
    search_params.set('price_max', document.getElementById("max_price").value.substring(1));

    // change the search property of the main url
    url.search = search_params.toString();

    // the new url string
    var new_url = url.toString();
    window.location.href = new_url;
}

function add_filter_price_button()
{
    var button_exists = document.getElementById("filter-price");
    if (button_exists == null) {
        var slider_form = document.getElementById("slider-form-group")
        var filter_price = `
                        <div class="col-xs-3 pt-3 py-2">
                            <button id="filter-price" onclick="set_price_parameters();return false;" type="button" class="btn btn-dark">Filter price</button>
                        </div>
                         `;
        slider_form.insertAdjacentHTML("beforeend", filter_price);
    }
}

function manage_filter_price(option){
    var can_add_button = validate_price(option);
    if(can_add_button){
        add_filter_price_button();
    }
}

(function ($) {
    'use strict';

$('#access-button').on('keypress click', function(e) {
    var value = $('#accessCodeInput').val();
    var CSRF_TOKEN = getCookie('csrftoken');
    if (e.which === 13 || e.type === 'click') {
        $.ajax({
            url: '/purchase/get_access/',
            headers: {
                'X-CSRFTOKEN': CSRF_TOKEN
            },
            data: {
                'ref_code': $('#ref_code').val(),
                'purchase_key': $('#purchase_key').val(),
                'access_code': $('#access_code').val()
            },
            success: purchaseSuccess,
            dataType: 'json',
        });
    }
});

function purchaseSuccess(data, textStatus, jqXHR)
{
    if(data.success){
        location.reload();
        return false;
    } else {
        alert('Access denied. Wrong access code.');
    }
}

$('#delete-purchase').on('click', function() {
    var q = confirm("Do you want to delete a purchase?");
    if (q == true) {
    var CSRF_TOKEN = getCookie('csrftoken');
        $.ajax({
            url: '/purchase/delete/',
            headers: {
                'X-CSRFTOKEN': CSRF_TOKEN
            },
            success: deletePurchase,
            dataType: 'json',
        });
    }
});

function deletePurchase(data)
{
    location.reload();
    alert("Purchase has been deleted.")
}

$('#delete-filter').click(function() {
    var url = new URL(window.location.href)
    var search_params = url.searchParams;

    var new_url = new URL(window.location.href)
    // set search property to blank
    new_url.search = '';
    var new_params = new_url.searchParams

    if (search_params.get('ordering')) {
        search_params.forEach(function(value, key) {
            if (key == 'ordering') {
                if (new_params.get('ordering')) {
                    new_params.append(key, value);
                } else {
                    new_params.append(key, value);
                }
            }
        });
        url.search = new_params.toString();
        var new_url = url.toString()
        window.location.href = url;
        //alert(url);
    } else {
        new_url.search = '';
        var new_url = new_url.toString();
        //alert(new_url);
        window.location.href = new_url;
    }
});

    var $window = $(window);

    // :: Nav Active Code
    if ($.fn.classyNav) {
        $('#essenceNav').classyNav();
    }

    $('#same-address').change(function() {
        var shippment_address = document.getElementById('shippment_address');
        if(shippment_address){
            if(shippment_address.style.display=='block'){
                shippment_address.style.display='none';
                this.checked = true;
            } else {
                shippment_address.style.display='block';
                this.checked = false;
            }

        }
    });
    $('#account-checkbox').change(function() {
        var create_account = document.getElementById('create-account');
        if(create_account){
            if(create_account.style.display=='block'){
                create_account.style.display='none';
            } else {
                create_account.style.display='block';
            }

        }
    });

$("div.search-area").on('touchstart click' ,function() {
    if ( $('#headerSearch').val() ) {
        if (!$('#search-result').is(':visible')){
            if(!$('#search-result').is(':empty')) {
                $('#search-result').show();
            }
        }
    }
});

$(document).mouseup(function(e)
{
    var container = $("div.search-area");
    if (!container.is(e.target) && container.has(e.target).length === 0)
    {
        if(!$('#search-result').is(':empty')) {
            $('#search-result').hide();
        }
    }
});

function search_ajax(){
        $.ajax({
            url: '/search/',
            type: 'POST',
            headers: {
                'X-CSRFTOKEN': getCookie('csrftoken')
            },
            data: {
                'search_text': $('#headerSearch').val()
            },
            success: searchSuccess,
            dataType: 'html',
        });
}

function process_promo_code(){
        var CSRF_TOKEN = getCookie('csrftoken');
        $.ajax({
            url: '/purchase/checkout/process_promo_code/',
            type: 'POST',
            headers: {
                'X-CSRFTOKEN': CSRF_TOKEN
            },
            data: {
                'code': $('#promo-code-input').val()
            },
            success: function(data) { promoCodeSuccess(data); },
            dataType: 'json',
        });
}

$("#promo-code-button").on('click' ,function() {
    if ( $('#promo-code-input').val() ) {
        process_promo_code()
    } else {
        alert('Incorrect input value');
    }
});


function promoCodeSuccess(data){
    alert(data['message']);
    if(data['promo_value']){
        $("#product-list-checkout").append(`<li class="list-group-item d-flex justify-content-between bg-light">
                <div class="text-success">
                  <h6 class="my-0">Promo code</h6>
                  <small>` + $('#promo-code-input').val() + `</small>
                </div>
                <span class="text-success">` + data['promo_value'] + `</span>
              </li>`
        );
        var cart_total = document.getElementById("checkout-cart-total")
        if(cart_total){
            cart_total.innerText=data['cart_total_value'];
        }
        $("#promo-div").remove();
    }
}

$("#search-button").on('touchstart click' ,function() {
    var search_text = document.getElementById('headerSearch');
    if (search_text.value.length > 1) {
        search_ajax()
    } else if (length < 1) {
        $("#search-result").html('');
        $("#search-result").hide();
    }
});

$("#headerSearch").on('keypress', function(e) {
    var search_text = document.getElementById('headerSearch');
    var length = search_text.value.length
    if (length > 1) {
        if (e.which == 13){
            search_ajax();
        }
    } else if (length < 1) {
        $("#search-result").html('');
        $("#search-result").hide();
    }
});

function searchSuccess(data, textStatus, jqXHR)
{
    $("#search-result").show();
    $('#search-result').html(data);
}

    // :: Sliders Active Code
    if ($.fn.owlCarousel) {
        $('.category-popular-products-slides').owlCarousel({
            items: 10,
            margin: 30,
            loop: true,
            nav: false,
            dots: false,
            autoplay: true,
            autoplayTimeout: 5000,
            smartSpeed: 1000,
            responsive: {
                0: {
                    items: 3
                },
                576: {
                    items: 5
                },
                768: {
                    items: 6
                },
                992: {
                    items: 8
                }
            }
        });
        $('.popular-products-slides').owlCarousel({
            items: 6,
            margin: 30,
            loop: true,
            nav: false,
            dots: false,
            autoplay: true,
            autoplayTimeout: 5000,
            smartSpeed: 1000,
            responsive: {
                0: {
                    items: 2
                },
                576: {
                    items: 3
                },
                768: {
                    items: 4
                },
                992: {
                    items: 6
                }
            }
        });
        $('.categories-slides').owlCarousel({
            items: 12,
            margin: 5,
            loop: true,
            nav: false,
            dots: false,
            autoplay: true,
            autoplayTimeout: 5000,
            smartSpeed: 1000,
            responsive: {
                0: {
                    items: 4
                },
                576: {
                    items: 6
                },
                768: {
                    items: 8
                },
                992: {
                    items: 12
                }
            }
        });
        $('.product_thumbnail_slides').owlCarousel({
            items: 1,
            margin: 0,
            loop: true,
            nav: true,
            navText: ["<img src='img/core-img/long-arrow-left.svg' alt=''>", "<img src='img/core-img/long-arrow-right.svg' alt=''>"],
            dots: false,
            autoplay: true,
            autoplayTimeout: 5000,
            smartSpeed: 1000
        });
    }

    // :: Header Cart Active Code
    var cartbtn1 = $('#essenceCartBtn');
    var cartOverlay = $(".cart-bg-overlay");
    var cartWrapper = $(".right-side-cart-area");
    var cartbtn2 = $("#rightSideCart");
    var cartOverlayOn = "cart-bg-overlay-on";
    var cartOn = "cart-on";

    cartbtn1.on('click', function () {
        cartOverlay.toggleClass(cartOverlayOn);
        cartWrapper.toggleClass(cartOn);
    });
    cartOverlay.on('click', function () {
        $(this).removeClass(cartOverlayOn);
        cartWrapper.removeClass(cartOn);
    });
    cartbtn2.on('click', function () {
        cartOverlay.removeClass(cartOverlayOn);
        cartWrapper.removeClass(cartOn);
    });

    // :: ScrollUp Active Code
    if ($.fn.scrollUp) {
        $.scrollUp({
            scrollSpeed: 1000,
            easingType: 'easeInOutQuart',
            scrollText: '<i class="fa fa-angle-up" aria-hidden="true"></i>'
        });
    }

    // :: Sticky Active Code
    $window.on('scroll', function () {
        if ($window.scrollTop() > 0) {
            $('.header_area').addClass('sticky');
        } else {
            $('.header_area').removeClass('sticky');
        }
    });

    // :: Nice Select Active Code
    if ($.fn.niceSelect) {
        $('select').niceSelect();
    }

    // :: Slider Range Price Active Code
    $('.slider-range-price').each(function () {
        var min = jQuery(this).data('min');
        var max = jQuery(this).data('max');
        var unit = jQuery(this).data('unit');
        var value_min = jQuery(this).data('value-min');
        var value_max = jQuery(this).data('value-max');
        var label_result = jQuery(this).data('label-result');
        var t = $(this);
        $(this).slider({
            range: true,
            min: min,
            max: max,
            values: [value_min, value_max],
            slide: function (event, ui) {
                var result = label_result + " " + unit + ui.values[0] + ' - ' + unit + ui.values[1];
                var input_min = document.getElementById("min_price")
                var input_max = document.getElementById("max_price")
                input_min.value = unit + ui.values[0]
                input_max.value = unit + ui.values[1]
                add_filter_price_button();
            }
        });
    });

    // :: Favorite Button Active Code
    var favme = $(".favme");

    favme.on('click', function () {
        $(this).toggleClass('active');
    });

    favme.on('click touchstart', function () {
        $(this).toggleClass('is_animating');
    });

    favme.on('animationend', function () {
        $(this).toggleClass('is_animating');
    });

    // :: Nicescroll Active Code
    if ($.fn.niceScroll) {
        $(".cart-list, .cart-content").niceScroll();
    }

    // :: wow Active Code
    if ($window.width() > 767) {
        new WOW().init();
    }

    // :: Tooltip Active Code
    if ($.fn.tooltip) {
        $('[data-toggle="tooltip"]').tooltip();
    }

    // :: PreventDefault a Click
    $("a[href='#']").on('click', function ($) {
        $.preventDefault();
    });

})(jQuery);