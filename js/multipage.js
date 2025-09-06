function createSpacer(spacerHeight){
    const spacer = document.createElement('div');
    spacer.className = 'spacer';
    spacer.style.cssText = `
        height: ${spacerHeight}mm;
    `;
    return spacer
}

// From : https://triss.dev/blog/units-on-the-web/
function toMM(p){
    return p / 3.78
}
function createMultiPageLayout(){
    const singleSpacer = false
    const content       = document.getElementsByClassName('canvas-container')
    const totalHeight   = content[0].scrollHeight
    const heightInMMs   = toMM(totalHeight)
    const totalPages    = Math.ceil(heightInMMs / 297)
    console.log('totalPages', totalPages);
    const children = content[0].children
    const numChildren = content[0].childElementCount
    const A4Height = 297
    if (totalPages > 1){
        var pageHeight = 0
        var pxHeight = 0.0
        let pageElements = []
        for (let c = 0; c < numChildren; c++) {
            pxHeight += children[c].scrollHeight

            var elementHeight = toMM(children[c].scrollHeight)
            var newPageHeight = pageHeight + elementHeight
            
            //console.log(elementHeight)
            console.log(c, ":" , newPageHeight)
            console.log(c, ":" , pxHeight)
            pageElements.push(children[c])
            if (newPageHeight > A4Height){
                //Create Spacer to full A4 page
                // Added height to brake pages (don't know why it's needed)
                const addedHeight = 5
                const spacerHeight = A4Height - pageHeight + addedHeight
                if (singleSpacer){
                    //Add spacer to page
                    console.log("New page : Inserting spacer before:",children[c])
                    spacer = createSpacer(spacerHeight)
                    content[0].insertBefore(spacer,children[c])
                }
                else
                {
                    const smallSpacerHeight = spacerHeight / (pageElements.length - 1)
                    print(pageElements)
                    for (let e = 1; e<pageElements.length; e++){
                        spacer = createSpacer(smallSpacerHeight)
                        content[0].insertBefore(spacer,pageElements[e])
                    }
                }
                
                pageElements = []
                pageHeight = elementHeight
            }
            else{
                pageHeight = newPageHeight
            }
        }
    }
}

window.addEventListener('load', createMultiPageLayout)