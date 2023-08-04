$( document ).ready(function() {
  // Shift nav in mobile when clicking the menu.
  $("[data-toggle='wy-nav-top']").click(function() {
    $("[data-toggle='wy-nav-shift']").toggleClass("shift");
    $("[data-toggle='rst-versions']").toggleClass("shift");
  });
  // Close menu when you click a link.
  $(".wy-menu-vertical .current ul li a").click(function() {
    $("[data-toggle='wy-nav-shift']").removeClass("shift");
    $("[data-toggle='rst-versions']").toggleClass("shift");
  });
  $("[data-toggle='rst-current-version']").click(function() {
    $("[data-toggle='rst-versions']").toggleClass("shift-up");
  });
  $("table.docutils:not(.field-list").wrap("<div class='wy-table-responsive'></div>");

  // styling fixes for api response tables
  $(".jh-type-object.jh-root").find(".jh-value").each(function() {
    $(this).css("padding", "5px").css("text-align", "left").css("vertical-align", "top");
  });
  $(".jh-type-object.jh-root").find(".jh-key").each(function() {
    $(this).css("padding", "5px").css("text-align", "left").css("vertical-align", "top");
  });
  $(".jh-type-object.jh-root").find("table").each(function() {
    $(this).css("border-collapse", "collapse");
    $(this).parent().css("padding", "0");
    $(this).css("border-style", "hidden");
  });
  $(".jh-root").children("tbody").children("tr").each(function() {
      $(this).children(".jh-object-key").css("background-color", "#f0f0f0");
  });
  $(".jh-type-object.jh-root")
    .css("border-collapse", "collapse");

});
