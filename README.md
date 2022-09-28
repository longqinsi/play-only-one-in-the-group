# play-only-one-in-the-group
An Anki Addon that allows to play only one item in a group during autoplaying Wrap a group of fields in a custom tag in order to play only one item in the group.

In the sample below, there are seven audios on the card, which are all wrapped in an only-one tag. If autoplay is enabled (this is the default case), only the first audio - hobby1 will be played. And if you press 'R' or 'F5', this audio will be replayed. But if you press 'N', the next audio in the group - hobby2 will be played, once again 'N' and hobby3, and so on, until the last audio hobby7, then back to the first one - hobby1. Instead, if you press 'P', there will a reversed playing order - hobby1, hobby7, hobby6, ..., hobby3, hobby2, hobby1, ... BTW, at any time if you press 'R' or 'F5', the audio last time played will be replayed, that may be any of hobby1, hobb2, ..., hobby7.
```html
<only-one>
    hobby1:{{hobby1}}<br/>
    hobby2:{{hobby2}}<br/>
    hobby3:{{hobby3}}<br/>
    hobby4:{{hobby4}}<br/>
    hobby5:{{hobby5}}<br/>
    hobby6:{{hobby6}}<br/>
    hobby7:{{hobby7}}<br/>
</only-one>
```
<b>P.S.</b> <i>I have added a shortcut Ctrl+R for replay on the review page, because each time when I am dictating in an input box, 'R' cannot be used, and F5 is not convenient.</i>
