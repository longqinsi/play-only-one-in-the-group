# play-only-one-in-the-group
An Anki Addon that allows to play only one item in a group during autoplaying
Wrap a group of fields in a custom tag <only-one> in order to play only one item in the group.

In the sample below, the media files in the fiels hobby1, hobby8 and hobby9 will always be 
played during the autoplay time when the card is loaded, but only one of hobby2, hobby3, hobby4
and only one of hobby5, hobby6 and hobby7 will be played. Which one in a group will be played is
random. If you press R or F5 to replay, the same list of items as when autoplaying will be 
played again.
```html
<div>hobby1:{{hobby1}}</div>
<only-one>
    hobby2:{{hobby2}}<br/>
    hobby3:{{hobby3}}<br/>
    hobby4:{{hobby4}}<br/>
</only-one>

<only-one>
    hobby5:{{hobby5}}<br/>
    hobby6:{{hobby6}}<br/>
    hobby7:{{hobby7}}<br/>
</only-one>

<div id='debugInfo'></div>
<script>
    console.log(`{{hobby8}}`);
</script>

<div style='font-family: "Arial"; font-size: 20px;'>hobby9:{{hobby9}}</div>
```
