export default
	[function(){
		return {
            truncateCrumbs: function(){
                let breadCrumbBarWidth = $('#bread_crumb').outerWidth();
                let menuLinkWidth = $('.BreadCrumb-menuLinkHolder').outerWidth();
                let availableWidth = breadCrumbBarWidth - menuLinkWidth;
                let $breadcrumbClone = $('.BreadCrumb-list').clone().appendTo('#bread_crumb_width_checker');
                let $breadcrumbCloneItems = $breadcrumbClone.find('.BreadCrumb-item');
                // 40px for the padding on the breadcrumb bar and a few extra pixels for rounding
				let breadcrumbBarPadding = 45;
                let expandedBreadcrumbWidth = breadcrumbBarPadding;
                let crumbs = [];
                $breadcrumbCloneItems.css('max-width', 'none');
                $breadcrumbCloneItems.each(function(index, item){
                    let crumbWidth = $(item).outerWidth();
                    expandedBreadcrumbWidth += crumbWidth;
                    crumbs.push({
                        index: index,
                        origWidth: crumbWidth
                    });
                });
                // Remove the clone from the dom
                $breadcrumbClone.remove();
                if(expandedBreadcrumbWidth > availableWidth) {
                    let widthToTrim = expandedBreadcrumbWidth - availableWidth;
                    // Sort the crumbs from biggest to smallest
                    let sortedCrumbs = _.orderBy(crumbs, ["origWidth"], ["desc"]);
                    let maxWidth;
                    for(let i=0; i<sortedCrumbs.length; i++) {
                        if(sortedCrumbs[i+1]) {
                            // This isn't the smallest crumb
                            if(sortedCrumbs[i-1]) {
                                // This isn't the biggest crumb
                                let potentialCrumbsToTrim = i+1;
                                if(potentialCrumbsToTrim*(sortedCrumbs[i].origWidth - sortedCrumbs[i+1].origWidth) > widthToTrim) {
                                    // If we trim down the biggest (i+1) crumbs equally then we can make it fit
                                    maxWidth = maxWidth - (widthToTrim/potentialCrumbsToTrim);
                                    break;
                                }
                                else {
                                    // Trim this biggest crumb down to the next biggest
                                    widthToTrim = widthToTrim - (sortedCrumbs[i].origWidth - sortedCrumbs[i+1].origWidth);
                                    maxWidth = sortedCrumbs[i].origWidth;
                                }
                            }
                            else {
                                // This is the biggest crumb
                                if(sortedCrumbs[i].origWidth - widthToTrim > sortedCrumbs[i+1].origWidth) {
                                    maxWidth = sortedCrumbs[i].origWidth - widthToTrim;
                                    break;
                                }
                                else {
                                    // Trim this biggest crumb down to the next biggest
                                    widthToTrim = widthToTrim - (sortedCrumbs[i].origWidth - sortedCrumbs[i+1].origWidth);
                                    maxWidth = sortedCrumbs[i+1].origWidth;
                                }
                            }
                        }
                        else {
                            // This is the smallest crumb
                            if(sortedCrumbs[i-1]) {
                                // We've gotten all the way down to the smallest crumb without being able to reasonably trim
                                // the previous crumbs.  Go ahead and trim all of them equally.
                                maxWidth = (availableWidth-breadcrumbBarPadding)/(i+1);
                            }
                            else {
                                // There's only one breadcrumb so trim this one down
                                maxWidth = sortedCrumbs[i].origWidth - widthToTrim;
                            }
                        }
                    }
                    $('.BreadCrumb-item').css('max-width', maxWidth);
                }
                else {
                    $('.BreadCrumb-item').css('max-width', 'none');
                }
            }
		};
	}];
