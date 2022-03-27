#include <stdio.h>
#include <stdlib.h>
#include "arm.h"
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <fcntl.h>
#include <errno.h>
#include <termios.h>
#include <unistd.h>


#define MAX_MEM 1024
#define LIFE 100
#define READ_SIZE 6

#define ACKMESSLEN 0
#define LORAWANHEADER 7


double ran_expo(double lambda);
double airtime(int SF,int CR, int pl, int bw);
//void update(double SFs[],int minSF,int SF,int acked,bool punish);
void update(int now_sf,int acked);
void simple_norm(double SFs[]);
//int random_pick_sf(double SFs[]);
int random_pick_sf(int minsf);

int epsilon = 0; // proba to not pick the best
int alpha = 1; // learning rate

int is_acked = -1;
int sf = 12;
int minsf = 12;

int SFs[6] = {0};


void printArmErr(armError_t err);



struct node {
    char* name; //adresse du port
    int period; // periode en ms
    int CR; // coding rate
    int BW; // bandwidth
    uint8_t SF; // spreading factor
    uint8_t minSF; // min spreading factor (suppose to depend of distance )
    double * SFs; // tableau de score
    int life; //temps de vie en secondes
    int send;   // nombre total d'envoie
    int retrans;    // nombre total de retransmission
    int acked;      //nombre total d'acquittement
};

int max(int* tab){
    int indice = 0;
    int max = tab[0];
    for(int i = 0 ; i<sizeof(tab) ; i++){
        if(tab[i] > max){
            max = tab[i];
            indice = i;
        }
    }
    return indice;
}

char* getData(){
    char cwd[256];
    printf("%s\n", getcwd(cwd, sizeof(cwd)));
    int status = 0;
    pid_t w;
    //pid_t cpid = system("python3 capteur_15.py");
    //pid_t cpid = system("python3 capteur_50.py");
    //pid_t cpid = system("python3 capteur_32.py");
    pid_t cpid = system("python3 capteur_40.py");
    printf("Cpid : %d\n", cpid);

    if (cpid == -1)
        printf("Erreur avec la command shell");
    else
    {
        printf("terminé, code=%d\n", WEXITSTATUS(status));
        do
        {
            w = waitpid(cpid, &status, WUNTRACED | WCONTINUED | SA_NOCLDWAIT);

            if (w == -1)
            {
                //perror("waitpid");
                break;
            }

            if (WIFEXITED(status))
            {
                printf("terminé, code=%d\n", WEXITSTATUS(status));
            }
            else if (WIFSIGNALED(status))
            {
                printf("tué par le signal %d\n", WTERMSIG(status));
            }
            else if (WIFSTOPPED(status))
            {
                printf("arrêté par le signal %d\n", WSTOPSIG(status));
            }
            else if (WIFCONTINUED(status))
            {
                printf("relancé\n");
            }
        }
        while (!WIFEXITED(status) && !WIFSIGNALED(status));
        //Lire le fichier + return
        FILE *file;
        char c;
        char* str = malloc(1024);
        strcpy(str, "");
        
        file = fopen("data.txt", "r");
        
        while (1)
        {
            c = fgetc(file);
            if (feof(file))
            {
                break;
            }
            strncat(str, &c, 1);
        }
            
        return str;
    }
    return "No data";
}


void simple_norm(double SFs[]){
    double s = 0;
    for (int i = 0 ; i < 6 ; i++){
        s += SFs[i];
    }
    for (int i = 0 ; i < 6 ; i++){
        SFs[i] /= s;
    }

}

/*
void update(double SFs[],int minSF,int SF,int acked,bool punish){
    if (acked){
        SFs[SF-7] *= (1 + 3*exp(-fabs(SF-minSF)));
    } else {
        if (punish){
            SFs[SF-7] *= 0.8;
        }else{
            SFs[SF-7] *= (0.05*exp(-fabs(SF-minSF))+0.85);
        }
    }
    simple_norm(SFs);

}*/

void update(int now_sf,int acked){
    SFs[now_sf-7] = SFs[now_sf-7] + alpha * (acked - SFs[now_sf-7]);
}

void transmit(arm_t* myArm,struct node *n,int confd){

    time_t t;
    double sleeping = 0;

    uint8_t lastSF = n->SF;

    uint8_t ltrans = 0;
    uint8_t last_airtime = 0;

    char* send = NULL;

    char* writer = NULL;
    writer = malloc(MAX_MEM);
    time_t starting = time(NULL);
    time_t actual = time(NULL);

    while ((actual - starting)< n->life){
        if(ltrans != 0 && ltrans < 8){
            n->retrans++;
            sleeping = fmax(2000+airtime(12,n->CR,ACKMESSLEN+LORAWANHEADER,n->BW),last_airtime*((1-0.01)/0.01)+ran_expo(1.0/2000))*1000; // calcul du temps d'attente entre 2 tentatives
            usleep(sleeping);
        }else{


            send = malloc(strlen(n->name)+1);
            printf("name:%s\n",send);
            strcpy(send,n->name);
            strcat(send,":");
            t = time(NULL);
            char* buffer = realloc(send,strlen(send) + 1 + strlen(ctime(&t)));
            assert(buffer != NULL);
            send = buffer;

            strcat(send,ctime(&t));

            sleeping = fmax(ran_expo(1.0/n->period),last_airtime*((1-0.01)/0.01))*1000;     //calcul du temps d'attente entre 2 transmissions
            usleep(sleeping);

        }

        n->send++;
        ltrans++;



        sprintf(writer,"%s: envoie du paquet %d / Tentatives n° %d avec le  SF%d\n",n->name,(n->send-n->retrans),ltrans,n->SF,lastSF);
        write(confd,writer,strlen(writer));
        printf("%s",writer+strlen(n->name)+2);


        char* data;
        data = getData();
        printf("Data : %s\n", data);

        armSend(myArm,data,strlen(data));
        uint8_t receivetest = 0;


        printf("Je choisis le SF %d\n",n->SF);
        receivetest = armReceive(myArm,data,sizeof(data),3000);
        printf("Message envoyé : %s\n",data);
        fflush(stdout);


        if (receivetest){
            sprintf(writer,"%s: Ack reçu pour le paquet %d\n",n->name,(n->send-n->retrans));
            write(confd,writer,strlen(writer));
            printf("Ack reçu pour le paquet %d \n",(n->send-n->retrans));
            fflush(stdout);
        } else {
            sprintf(writer,"%s: Ack non reçu pour le paquet %d\n",n->name,(n->send-n->retrans));
            write(confd,writer,strlen(writer));
            printf("Ack non reçu pour le paquet %d \n",(n->send-n->retrans));
            fflush(stdout);
        }



        last_airtime = airtime(n->SF,n->CR,strlen(send),n->BW);
        bool punish_on = false;
        if (receivetest != 0 ){             // vérifie l'acquittement
            n->acked++;
            free(send);
            ltrans = 0;
            update(n->SF,1);
        } else {
            double x = rand() / (RAND_MAX + 1.0);
            if (x < n->SFs[n->SF-7]){
                punish_on = true;
            }
            update(n->SF,0);              // met à jour le tableau de score
        }

        n->SF = random_pick_sf(minsf);
        fflush(stdout);
        armLwGetRadio(myArm,NULL,NULL,&lastSF,NULL,NULL);
        armError_t e = armLwSetRadio(myArm,0,0,n->SF,12,0);
        armUpdateConfig(myArm);                                     // change les configurations de la carte
        if (e!=ARM_ERR_NONE){
            printArmErr(e);
            return ;
        }
        if (ltrans == 8){
            free(send);
        }
        printf("\n");
        actual = time(NULL);

    }

    t = time(NULL);
    printf("J'ai fini a %s\n",ctime(&t));
    fflush(stdout);
    free(writer);
}

/*
int random_pick_sf(double SFs[]){
    int x = 0;
    double cumulative_prob = 0;
    double u = rand() / (RAND_MAX + 1.0);
    for (int i = 0 ; i < 6 ; i ++){
        cumulative_prob += SFs[i];
        if (u < cumulative_prob){
            x = i;
            break;
        }
    }
    return x + 7;
}*/

int random_pick_sf(int minsf){
    int x = rand() %2;
    if (x > epsilon)
        return max(SFs) + 7;
    else{
        int x = (rand() % (13-minsf)) + minsf;
        return x;
    }

}

double ran_expo(double lambda){
    double u = 0;

    u = rand() / (RAND_MAX + 1.0 );

    return -log(1 - u) / lambda;

}

double airtime(int SF,int CR,int pl ,int bw){
    int H = 0;
    int DE = 0;
    int Npream = 8;

    if (bw == 125 && (SF == 11 || SF==12)){
        DE = 1;
    }


    double Tsym = pow(2.0,(double)SF);
    double Tpream = (Npream + 4.25) * Tsym;

    int payloadSymbNB = 8 + fmax(ceil((8.0*pl-4.0*SF+28+16-20*H)/(4.0*(SF-2*DE)))*(CR+4),0);
    int Tpayload = payloadSymbNB * Tsym;
    return (Tpream + Tpayload);

}



void minsf_cut(struct node *n,double alpha){
    int min = n->minSF - 7;
    for (int i = 0 ; i < min; i ++){
        n->SFs[i] = 0;
    }

    for (int i = min; i < 6 ; i ++ ){
        n->SFs[i] = exp(-alpha*abs(min-i));
    }
    simple_norm(n->SFs);
}


int main(int argc,char* argv[])
{
    
    
    printf("starting main\n");
    int total_send = 0;
    int total_retransmission = 0;
    int total_acked = 0;


    if(argc != 3 ){
        printf("Not right number of args\n");
        return -1;
    }

    FILE* settings = fopen(argv[2],"r");
    if(settings == NULL){
        printf("File %s not found.\n",argv[2]);
        return -1;
    }

    char* reading = malloc(MAX_MEM);
    char* out;
    out = "";

    char* port = "/dev/ttyUSB";
    int enough = 0;


    int nbrnode = strtol(argv[1],NULL,10);

    int pid[nbrnode];

    struct node n;

    int i = 0;

    int j = 2;

    int period = 0;
    int sf = 0;
    int life = 0;

    arm_t myArm;
            
    

    for (i = 0 ; i < nbrnode ; i++){            // méthode complexe d'initialisation des noeuds

        fgets(reading,MAX_MEM,settings);
        if (!feof(settings)){           // parse les paramètres du noeuds
            out = strtok(reading," ");
            period = strtol(out,NULL,10)*1000;
            out = strtok(NULL," ");
            sf = strtol(out,NULL,10);
            out = strtok(NULL," ");
            life = strtol(out,NULL,10);
        }

        pid_t p = fork();
        if (p == 0){

            //name
            enough = ceil(log10(i+1)) + 2;
            char* numberbuff = malloc(enough);
            sprintf(numberbuff,"%d",i);
            n.name = malloc(strlen(port)+enough);
            strcpy(n.name,port);
            strcat(n.name,numberbuff);
            free(numberbuff);

            //default value
            n.CR = 1;
            n.BW = 125;
            n.period = 10000;
            n.SF = 7;
            n.minSF = 7;
            n.SFs = malloc(6*sizeof(double));
            n.life = LIFE;
            n.send = 0;
            n.retrans = 0;
            n.acked = 0;

            for (int k = 0; k < 6 ; k ++ ){
                n.SFs[k] = 1./6;
            }

            if(!feof(settings)){    //donne les paramètres aux noeuds
                n.period = period;
                n.life = life;
                if(sf > 6 && sf < 13){
                    n.minSF = sf;
                    n.SF = sf;
                    minsf_cut(&n,2);
                }
            }
            break;
        }
	
        pid[i] = p;
        j+=2;

    }


    free(reading);
    fclose(settings);

    if (i < nbrnode){

        int saveout = dup(STDOUT_FILENO);

 
    char* writer = NULL;
    writer = malloc(MAX_MEM);
    
    
        strcpy(out,"log/");
        strcat(out,n.name+8);   // Le nom du log a partir du USBX de la carte


        int logout = open(out,O_WRONLY | O_CREAT | O_TRUNC,S_IRWXU|S_IRWXG|S_IROTH);    //ouvre le fichier de log
        if (logout == -1){
            free(n.name);
            free(n.SFs);
            close(logout);
            return -1;
        } else{
            close(STDOUT_FILENO);
            dup2(logout,1);
            
        }


        srand(i*time(NULL));        // donne une seed aléatoire différente à chaque noeud

        armError_t e = armInit(&myArm,n.name);
        if (e != ARM_ERR_NONE){
            printArmErr(e);
            free(n.name);
            free(n.SFs);
            return -1;
        }



        armLwEnableDutyCycle(&myArm,true);
        armLwSetConfirmedFrame(&myArm,1);
        e = armUpdateConfig(&myArm);
        if (e!=ARM_ERR_NONE){
            printArmErr(e);
            free(n.name);
            free(n.SFs);
            return -1;
        }
        armLwSetRadio(&myArm,0,0,n.SF,12,0);
        armUpdateConfig(&myArm);


        transmit(&myArm,&n,saveout);
        printf("=======Stats======\n");
        printf("Nombre_d_envoie: %d\n",n.send);
        printf("Nombre_de_retransmission: %d\n",n.retrans);
        printf("Nombre_d_acquittement: %d\n",n.acked);
        fflush(stdout);


        dup2(saveout,STDOUT_FILENO);
        printf("Ending : %s\n",n.name);

        close(logout);
        free(n.name);
        free(n.SFs);
        armDeInit(&myArm);
    } else {
        printf("All Nodes Launched\n");
        for (int k = 0 ; k < nbrnode;k++){
            bool get_stat = true;
            waitpid(pid[k],NULL,0);
            FILE* stat;
            reading = malloc(MAX_MEM);
            char* name = malloc(MAX_MEM);
            strcpy(name,"log/USB");
            char* number = malloc(ceil(log10(k+1))+1);
            sprintf(number,"%d",k);
            strcat(name,number);
            free(number);
            stat = fopen(name,"r");
            fgets(reading,MAX_MEM,stat);
            while(reading[0] !='='){
                fgets(reading,MAX_MEM,stat);
                if(feof(stat)){
                get_stat = false;
                    break;
                }
            }
            if (get_stat){
                fgets(reading,MAX_MEM,stat);
                out = strtok(reading," ");
                out = strtok(NULL," ");
                total_send += strtol(out,NULL,10);
                fgets(reading,MAX_MEM,stat);
                out = strtok(reading," ");
                out = strtok(NULL," ");
                total_retransmission += strtol(out,NULL,10);
                fgets(reading,MAX_MEM,stat);
                out = strtok(reading," ");
                out = strtok(NULL," ");
                total_acked += strtol(out,NULL,10);
            }
            free(reading);
            fclose(stat);
        }
        printf("Total Send : %d\n",total_send);
        printf("Total Resend : %d\n",total_retransmission);
        printf("Total Acked : %d\n",total_acked);
    }



    return 0;
}


void printArmErr(armError_t err)
{
	switch(err)
	{
		case ARM_ERR_NONE:
			printf("ARM_ERR_NONE: 'No error.'\r\n");
		break;

		case ARM_ERR_NO_SUPPORTED:
			printf("ARM_ERR_NO_SUPPORTED: 'Functionality no supported by theARM.'\r\n");
		break;

		case ARM_ERR_PORT_OPEN:
			printf("ARM_ERR_PORT_OPEN: 'Port Error, at the port opening.'\r\n");
		break;

		case ARM_ERR_PORT_CONFIG:
			printf("ARM_ERR_PORT_CONFIG: 'Port Error, at the port configuring.'\r\n");
		break;

		case ARM_ERR_PORT_READ:
			printf("ARM_ERR_PORT_READ: 'Port Error, at the port reading.'\r\n");
		break;

		case ARM_ERR_PORT_WRITE:
			printf("ARM_ERR_PORT_WRITE: 'Port Error, at the port writing.'\r\n");
		break;

		case ARM_ERR_PORT_WRITE_READ:
			printf("ARM_ERR_PORT_WRITE_READ: 'Port Error, at the port reading/writing.'\r\n");
		break;

		case ARM_ERR_PORT_CLOSE:
			printf("ARM_ERR_PORT_CLOSE: 'Port Error, at the port closing.'\r\n");
		break;

		case ARM_ERR_PARAM_OUT_OF_RANGE:
			printf("ARM_ERR_PARAM_OUT_OF_RANGE: 'Error, one or more of parameters is out of range.'\r\n");
		break;

		case ARM_ERR_PARAM_INCOMPATIBLE:
			printf("ARM_ERR_PARAM_INCOMPATIBLE: 'Error, the parameters is incompatible between them.'\r\n");
		break;

		case ARM_ERR_ADDRESSING_NOT_ENABLE:
			printf("ARM_ERR_ADDRESSING_NOT_ENABLE: 'Error, the addressing is not enable.'\r\n");
		break;

		case ARM_ERR_WOR_ENABLE:
			printf("ARM_ERR_WOR_ENABLE: 'Error, the WOR mode is enable.'\r\n");
		break;

		case ARM_ERR_ARM_GO_AT:
			printf("ARM_ERR_ARM_GO_AT: 'ARM commend Error, can't switch to AT commend.'\r\n");
		break;

		case ARM_ERR_ARM_BACK_AT:
			printf("ARM_ERR_ARM_BACK_AT: 'ARM commend Error, can't quit AT commend.'\r\n");
		break;

		case ARM_ERR_ARM_CMD:
			printf("ARM_ERR_ARM_CMD: 'ARM commend Error, from AT commend.'\r\n");
		break;

		case ARM_ERR_ARM_GET_REG:
			printf("ARM_ERR_ARM_GET_REG: 'ARM commend Error, from get register.'\r\n");
		break;

		case ARM_ERR_ARM_SET_REG:
			printf("ARM_ERR_ARM_SET_REG: 'ARM commend Error, from set register.'\r\n");
		break;

		default:
			printf("ARM_ERR_UNKNON: 'Error unknown'\r\n");
		break;
	}
}


