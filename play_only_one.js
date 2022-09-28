//The following guid is to avoid duplicated import of this file on answer side: 614c0753-ddb7-4818-87df-979fe0670a48

(() => {
    for (let only_one of document.getElementsByTagName('only-one')) {
        if (only_one.getElementsByClassName('replay-button soundLink').length > 1) {
            only_one.classList.add('has_multiple_av_tags');
        }
    }
})();

/**
 * @param {Number[]} current_av_indices The list of indices currently to play
 * @param {string} side The card side, 'question' or 'answer'
 */
function paint_current_av_tags(current_av_indices, side) {
    const regexp = side === 'question' ? /(?<=pycmd\('play:q:)(\d+)(?='\); return false;)/
        : /(?<=pycmd\('play:a:)(\d+)(?='\); return false;)/;
    for (let av_tag of document.querySelectorAll('a.replay-button.soundLink')) {
        let av_tag_index_match = av_tag.getAttribute('onclick').match(regexp);
        if (av_tag_index_match) {
            let av_tag_index = parseInt(av_tag_index_match[0]);
            if (current_av_indices.includes(av_tag_index)) {
                av_tag.classList.add('current');
            } else {
                av_tag.classList.remove('current');
            }
        }
    }
}
