function download_data(){
    gsutil cp -rn gs://smart-vpa/data.zip ~/smart-vpa/data
    unzip ~/smart-vpa/data/data.zip -d ~/smart-vpa/data/
    mv  ~/smart-vpa/data/data/* ~/smart-vpa/data/ 
    rm -r ~/smart-vpa/data/data
    rm -r ~/smart-vpa/data/data.zip
}

download_data