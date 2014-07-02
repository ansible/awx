/*!
 * jPushMenu.js
 * 1.1.1
 * @author: takien
 * http://takien.com
 * Original version (pure JS) is created by Mary Lou http://tympanus.net/
 */

(function($) {
    $.fn.jPushMenu = function(customOptions) {
        var jPushMenu,
            o = $.extend({}, $.fn.jPushMenu.defaultOptions, customOptions);

        /* add class to the body.*/

        $('body').addClass(o.bodyClass);
        $(this).addClass('jPushMenuBtn');
        $(this).click(function() {
            var target         = '',
            push_direction     = '';

            if($(this).is('.'+o.showLeftClass)) {
                target         = '.cbp-spmenu-left';
                push_direction = 'toright';
            }
            else if($(this).is('.'+o.showRightClass)) {
                target         = '.cbp-spmenu-right';
                push_direction = 'toleft';
            }
            else if($(this).is('.'+o.showTopClass)) {
                target         = '.cbp-spmenu-top';
            }
            else if($(this).is('.'+o.showBottomClass)) {
                target         = '.cbp-spmenu-bottom';
            }


            $(this).toggleClass(o.activeClass);
            $(target).toggleClass(o.menuOpenClass);

            if ($(this).is('.'+o.pushBodyClass)) {
                $('body').toggleClass( 'cbp-spmenu-push-'+push_direction );
            }

            /* disable all other button*/
            $('.jPushMenuBtn').not($(this)).toggleClass('disabled');

            return false;
        });
        jPushMenu = {
            close: function () {
                $('.jPushMenuBtn,body,.cbp-spmenu').removeClass('disabled active cbp-spmenu-open cbp-spmenu-push-toleft cbp-spmenu-push-toright');
            }
        };

        if (o.closeOnClickInside) {
            $(document).click(function() {
                jPushMenu.close();
            });

            $('.cbp-spmenu,.toggle-menu').click(function(e){
                e.stopPropagation();
            });
        }

        if (o.closeOnClickOutside) {
            $(document).click(function() {
                jPushMenu.close();
            });

            $('.cbp-spmenu,.toggle-menu').click(function(e){
                e.stopPropagation();
            });
         }

        // On Click Link
        if (o.closeOnClickLink) {
            $('.cbp-spmenu a').on('click',function(){
                jPushMenu.close();
            });
        }
    };
   /*  in case you want to customize class name,
    *  do not directly edit here, use function parameter when call jPushMenu.
    */
    $.fn.jPushMenu.defaultOptions = {
        bodyClass       : 'cbp-spmenu-push',
        activeClass     : 'menu-active',
        showLeftClass   : 'menu-left',
        showRightClass  : 'menu-right',
        showTopClass    : 'menu-top',
        showBottomClass : 'menu-bottom',
        menuOpenClass   : 'cbp-spmenu-open',
        pushBodyClass   : 'push-body',
        closeOnClickOutside: true,
        closeOnClickInside: true,
        closeOnClickLink: true
    };
})(jQuery);