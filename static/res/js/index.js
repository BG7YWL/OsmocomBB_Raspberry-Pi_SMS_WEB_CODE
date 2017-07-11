$(document).ready(function() {
	$('.loading').css({"width":$(window).width(),"height":$(window).height()});
	hacksms.getUSB();
});

var hacksms = {
	getUSB:function(){
		$.post('/getUSB', {}, function(data, textStatus, xhr) {
			
			if(data.total == 0){
				$('.device').html('<p class="nodevice">未发现可用设备</p>');
				return;
			}

			if(data.rows[0] != '/dev/ttyUSB0'){
				alert('设备初始化异常，请尝试重新插拔');
				return;
			}

			$('.device').empty();

			for(var dev = 1;dev < data.total;dev++){
				$('.device').append(
					'<div class="col-md-3 devItem" id="device_'+ dev +'" data-dev="'+ data.rows[dev] +'">'+
		                '<div class="panel panel-primary">'+
		                    '<div class="panel-heading clearfix itemHeader">'+
		                    	'<b>'+ data.rows[dev] +'</b>'+
		                    	'<button class="btn btn-xs btn-primary pull-right itemscan" onclick="hacksms.scanARFCN(this)">扫描</button>'+
		                    	'<button class="btn btn-xs btn-primary pull-right" onclick="hacksms.download(this)">刷机</button>'+
		                    '</div>'+
		                    '<div class="panel-body itemARFCN">'+
		                    	'<p class="scanDate"></p>'+
		                    	'<table cellpadding="0" cellspacing="0">'+
			                    	'<thead>'+
			                            '<tr>'+
			                                '<th width="50px">ARFCN</th>'+
			                                '<th>信号</th>'+
			                                '<th>类型</th>'+
			                                '<th width="60px">操作</th>'+
			                            '</tr>'+
			                        '</thead>'+
			                        '<tbody>'+
			                        '</tbody>'+
			                    '</table>'+
		                    '</div>'+
		                '</div>'+
		            '</div>'
				);
			}

			hacksms.initARFCN();

		},"json");
	},
	killdev:function(){
		$.post('/killdev', {}, function(data, textStatus, xhr) {
			if(data.res == 0){
				alert('操作成功!');
			}else{
				alert('发生异常:'+data.msg);
			}
		},"json");
	},
	resetPower:function(){
		$('.loading').show();
		$.post('/resetPower', {}, function(data, textStatus, xhr) {
			$('.loading').hide();
			if(data.res == 0){
				alert('操作成功!');
			}else{
				alert('发生异常:'+data.msg);
			}
		},"json");
	},
	downloadAll:function(){
		$.post('/downloadAll', {}, function(data, textStatus, xhr) {
			$('.loading').show();
			if(data.res == 0){
				alert('刷机完成!');
			}else{
				alert('发生异常:'+data.msg);
			}
		},"json");
	},
	download:function(obj){
		var object = $(obj),devid = object.parents('.devItem').attr('data-dev');
		$('.loading').show();
		$.post('/download', {"devid":devid}, function(data, textStatus, xhr) {
			$('.loading').hide();
			if(data.res == 0){
				
			}else{
				alert('发生异常:'+data.msg);
			}
		},"json");
	},
	initARFCN:function(){
		var items = $('.devItem');

		for(var i = 0;i < items.length;i++){
			$.ajax({  
	         	type : "POST",  
	          	url : "/readARFCN", 
	          	dataType:"json", 
	          	data : {"devid":items.eq(i).attr('data-dev').split('USB')[1]},  
	          	async : false,  
	          	success : function(data){  
	            	if(data.res == 0){
						items.eq(i).find('tbody').empty();
						items.eq(i).find('.scanDate').text('最近扫描: '+data.date);
						for(var arfcn = 0;arfcn < data.rows.length;arfcn++){
							var thisARFCNArr = data.rows[arfcn].split(' ');
							items.eq(i).find('tbody').append(
								'<tr>'+
		                            '<td>'+ thisARFCNArr[0].split('=')[1] +'</td>'+
		                            '<td>'+ thisARFCNArr[1].split('=')[1] +'</td>'+
		                            '<td>'+ thisARFCNArr[6].replace(')','') +'</td>'+
		                            '<td><button class="btn btn-primary" onclick="hacksms.sniff('+ data.rows[arfcn].split(' ')[0].split('=')[1] +',\''+ items.eq(i).attr('data-dev') +'\')">嗅探</button></td>'+
		                        '</tr>'
							);
						}
						if(data.rows.length<1){
							items.eq(i).find('tbody').html('<tr><td colspan="4" style="color:#c00">未扫描</td></tr>');
						}
					}else{
						alert('发生异常:'+data.msg);
					}
	          	}  
		     });
		}
	},
	scanAll:function(){
		var devLength = $('.devItem').length,oneKeyTimer,devIndex = 0;
		
		oneKeyTimer = setInterval(function(){
			if(devIndex < devLength){
				$('.itemscan').eq(devIndex).click();
				devIndex++;
			}else{
				clearInterval(oneKeyTimer);
			}
		},1000);
		
	},
	scanARFCN:function(obj){
		var object = $(obj),thisMain = object.parents('.devItem'),devid = thisMain.attr('data-dev');
		$('.loading').show();
		$.post('/getARFCN', {"devid":devid}, function(data, textStatus, xhr) {
			$('.loading').hide();
			if(data.res == 0){
				thisMain.find('tbody').empty();
				thisMain.find('.scanDate').text('最近扫描: '+data.date);
				for(var arfcn = 0;arfcn < data.rows.length;arfcn++){
					var thisARFCNArr = data.rows[arfcn].split(' ');
					thisMain.find('tbody').append(
						'<tr>'+
                            '<td>'+ thisARFCNArr[0].split('=')[1] +'</td>'+
                            '<td>'+ thisARFCNArr[1].split('=')[1] +'</td>'+
                            '<td>'+ thisARFCNArr[6].replace(')','') +'</td>'+
                            '<td><button class="btn btn-primary" onclick="hacksms.sniff('+ data.rows[arfcn].split(' ')[0].split('=')[1] +',\''+ devid +'\')">嗅探</button></td>'+
                        '</tr>'
					);
				}
				if(data.rows.length<1){
					thisMain.find('tbody').html('<tr><td colspan="4" style="color:#c00">未扫描</td></tr>');
				}
			}else{
				alert('发生异常:'+data.msg);
			}
		},"json");
	},
	sniff:function(arfcn,devid){
		$.post('/doSniffer', {"arfcn":arfcn,"devid":devid}, function(data, textStatus, xhr) {
			if(data.res == 0){
				console.log('操作成功! PID: '+data.pid);
			}else{
				alert('发生异常:'+data.msg);
			}
		},"json");
	}
}