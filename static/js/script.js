/*
Template Name: Dactorapp - Doctor Appointment Booking Mobile Template
Author: Askbootstrap
Author URI: https://themeforest.net/user/askbootstrap
Version: 0.1
*/

/*
- Sidebar
- Landing Page
- Homepage
- Video Page
*/

(function ($) {
    "use strict"; // Start of use strict

    // Sidebar
    var $main_nav = $('#main-nav');
    var $toggle = $('.toggle');

    var defaultOptions = {
        disableAt: false,
        customToggle: $toggle,
        levelSpacing: 40,
        navTitle: 'Dactorapp',
        levelTitles: true,
        levelTitleAsBack: true,
        pushContent: '#container',
        insertClose: 2
    };
    var Nav = $main_nav.hcOffcanvasNav(defaultOptions);

    // Landing Page
    $('.landing-slider').slick({
        dots: true,
        autoplay: true,
        nextArrow: false,
        prewArrow: false,
    });

    // Homepage
    $('.top-doctors').slick({
        infinite: false,
        dots: false,
        arrows: false,
        speed: 300,
        autoplay: false,
        slidesToShow: 2.2,
        slidesToScroll: 1,
    });

    $('.available-doctor').slick({
        infinite: false,
        dots: false,
        arrows: false,
        speed: 300,
        autoplay: false,
        slidesToShow: 1.2,
        slidesToScroll: 1,
    });

    // Video Page
    $('.recent-doctors').slick({
        infinite: false,
        dots: false,
        arrows: false,
        speed: 300,
        autoplay: false,
        slidesToShow: 2.2,
        slidesToScroll: 1,
    });

})(jQuery);

