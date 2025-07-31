 ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    # 更换为阿里云镜像源加速下载
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    # 安装系统依赖
    apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsm6 \
        libxext6 \
        curl 
 
\
        && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

sudo ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
sudo echo $TZ > /etc/timezone && \
sudo sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
sudo sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
sudo apt-get update && \
sudo apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl


<table><caption>Table Location: 5 安徽省引江济淮集团有限公司工程管理条件20221023 > 3 管理条件 > 附录A</caption><tr><td>序号</td><td>管理条件</td><td>配	置	要	求</td></tr><tr><td>1</td><td>挡鼠板</td><td>配备40cm高的的挡鼠板，并张贴必要的警示标志</td></tr><tr><td>2</td><td>风机</td><td>根据现场面积配置风机，以改善设备设施运行环境</td></tr><tr><td>3</td><td>摄像机</td><td>配备高清固定枪式摄像机，满足对开关柜的全方位监视（昼夜）</td></tr><tr><td>4</td><td>绝缘垫</td><td>在柴油发电机组四周铺设8mm厚的绝缘橡胶垫</td></tr><tr><td>5</td><td>温湿度监测装置</td><td>数字式温湿度监测仪或传感器，按规范要求进行巡视或记录</td></tr><tr><td>6</td><td>警示线</td><td>在绝缘垫周围粘贴黄黑色警示线，提醒请勿靠近</td></tr><tr><td>7</td><td>消防设施</td><td>按消防设计要求配备灭火器、消防沙箱</td></tr><tr><td>8</td><td>运行记录表</td><td>配备设备运行记录表，在设备运行时及时填写记录</td></tr><tr><td>9</td><td>照明设施</td><td>配备的日常和事故照明灯具，以及应急逃生指示灯</td></tr><tr><td>10</td><td>巡视路线标识</td><td>在地面粘贴巡视路线标识，并注明关键巡视点及巡视内容</td></tr><tr><td>11</td><td>功能区标识</td><td>在门口设置“柴油发电机房”标示门牌，参照标识标牌标准</td></tr><tr><td>12</td><td>安全告知牌</td><td>在入口配置安全警示警告系列标识，参照标识标牌</td></tr><tr><td>13</td><td>主要巡视
检查内容</td><td>参照标识标牌标准设计制作，明确日常及运行时的主要巡视内容和周期</td></tr><tr><td>14</td><td>危险源告知牌</td><td>参照标识标牌标准设计制作，提醒管理人员柴油发电机房存在触电、火灾、爆炸等危险源，应采取必要的防范措施</td></tr><tr><td>15</td><td>职业危害告知牌</td><td>参照标识标牌标准设计制作，提醒管理人员柴油发电机房存在噪声职业危害，应采取必要的防范措施</td></tr><tr><td>16</td><td>整机噪音</td><td>当电动机单台功率<30kW时不应大于85 dB(A)，≥30 kW时不应大于90 dB(A)</td></tr></table>


http://47.117.45.109:20007/app/20f203dd-8e28-4a9a-92d4-a8c5c95b7d58/workflow#:~:text=%E4%BF%9D%E9%9A%9C%E3%80%82%0A36b04ec896c64d168d83d6a41a68bb2e.docx-,36b04ec896c64d168d83d6a41a68bb2e,-.docx

http://47.117.45.109:20007/files/tools/8a93fd5d-4f21-4414-ab5e-ba7e73c64a98.docx?timestamp=1753927868&nonce=d307e58dcc9a511b2628f6b9751bd769&sign=nbuY6TiBpVRFJQgn56CMV6f0UlouPCum3F4vivTRXt4=&as_attachment=true

http://47.117.45.109:20007/files/tools/8a93fd5d-4f21-4414-ab5e-ba7e73c64a98.docx?timestamp=1753927868&nonce=960ba85501cf62cd235fdf4ce54e0446&sign=XRp_kewycrR6cEJkQ1qcM2O3r1bS6kYddG5SmvSQD0c=&as_attachment=true

http://47.117.45.109:20007/files/tools/8a93fd5d-4f21-4414-ab5e-ba7e73c64a98.docx?timestamp=1753927868&nonce=07cdc4cf3a6c24b72f29200a383ff31a&sign=r_dx81JZWISeZ7Mm7VaNJui8fLMkdSSZ4G5kDoDcGjY=


curl -X GET \
  "http://47.117.45.109:20007/files/tools/8a93fd5d-4f21-4414-ab5e-ba7e73c64a98.docx?timestamp=1753927868&nonce=d307e58dcc9a511b2628f6b9751bd769&sign=nbuY6TiBpVRFJQgn56CMV6f0UlouPCum3F4vivTRXt4=&as_attachment=true" \
  -H "Authorization: Bearer app-W1fb9flI4juhc6jcjIUgLMRj"