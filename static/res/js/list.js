$(document).ready(function() {
	hacksms.getSMS()；
	setInterval(function(){hacksms.getSMS();},3000);
});

var hacksms = {
	getSMS:function(){
		$.post('/getSMS', {"page":1,"rows":1000}, function(data, textStatus, xhr) {
			if(data.res == 0){
				$('.smsList').find('tbody').empty();
				for(var s = 0;s<data.rows.length;s++){
					$('.smsList').find('tbody').append(
						'<tr>'+
                            '<td class="tdid">'+ data.rows[s].id +'</td>'+
                            '<td>'+ data.rows[s].phone +'</td>'+
                            '<td>'+ data.rows[s].center +'</td>'+
                            '<td style="text-align:left;padding:0 10px">'+ data.rows[s].content.replace('<','&lt;').replace('>','&gt;') +'</td>'+
                            '<td>'+ data.rows[s].type +'</td>'+
                            '<td>'+ data.rows[s].date +'</td>'+
                        '</tr>'
					);
				}
			}else{
				alert('发生异常:'+data.msg);
			}
		},"json");
	}
}
