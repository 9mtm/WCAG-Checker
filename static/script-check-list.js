$(document).ready(function () {

  // apply line-through CSS to checked SCs
  $("input:checkbox").live("click", function () {
    $(this).parent("li").toggleClass("checked");
  });

  $("fieldset input:checkbox").on("click", function (e) {
    // logic here modified from: http://3pha.com/wcag2/
    var version2_0 = $("#wcag20")[0].checked;
    var version2_1 = $("#wcag21")[0].checked;
    var version2_2 = $("#wcag22")[0].checked;

    var levelA = $("#levela")[0].checked;
    var levelAA = $("#levelaa")[0].checked;
    var levelAAA = $("#levelaaa")[0].checked;

    // LEVEL A
    if (levelA) {
      $(".levela").show();
      if (!version2_0) $(".wcag20").hide();
      if (!version2_1) $(".wcag21").hide();
      if (!version2_2) $(".wcag22").hide();
    } else {
      $(".levela").hide();
    }

    // LEVEL AA
    if (levelAA) {
      $(".levelaa").show();
      if (!version2_0) $(".wcag20").hide();
      if (!version2_1) $(".wcag21").hide();
      if (!version2_2) $(".wcag22").hide();
    } else {
      $(".levelaa").hide();
    }

    // LEVEL AAA
    if (levelAAA) {
      $(".levelaaa").show();
      if (!version2_0) $(".wcag20").hide();
      if (!version2_1) $(".wcag21").hide();
      if (!version2_2) $(".wcag22").hide();
    } else {
      $(".levelaaa").hide();
    }
    
    // Count visible SCs and update
    var visibleCount_wcag20 = $(".wcag20:visible").length;
    var visibleCount_wcag21 = $(".wcag21:visible").length;
    var visibleCount_wcag22 = $(".wcag22:visible").length;
    $("#currentScCount").text(visibleCount_wcag20 + visibleCount_wcag21 + visibleCount_wcag22);
  });

  //zebra stripe list items
  $("li:even").addClass("stripe");
});